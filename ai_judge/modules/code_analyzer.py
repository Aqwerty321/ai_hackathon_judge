from __future__ import annotations

import ast
import contextlib
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

try:  # pragma: no cover - optional dependency during tests
    from pylint.lint import Run as PylintRun
    from pylint.reporters.collecting import CollectingReporter
except ImportError:  # pragma: no cover - executed when pylint missing
    PylintRun = None  # type: ignore
    CollectingReporter = None  # type: ignore

try:  # pragma: no cover - optional dependency during tests
    from radon.complexity import cc_visit
except ImportError:  # pragma: no cover
    cc_visit = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None  # type: ignore


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CodeAnalysisResult:
    """Metrics summarising code quality aspects."""

    readability_score: float
    documentation_score: float
    test_coverage_score_estimate: float
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        details = json.loads(json.dumps(self.details))
        return {
            "readability_score": self.readability_score,
            "documentation_score": self.documentation_score,
            "test_coverage_score_estimate": self.test_coverage_score_estimate,
            "details": details,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CodeAnalysisResult":
        details = data.get("details")
        if not isinstance(details, Mapping):
            details = {}
        return cls(
            readability_score=float(data.get("readability_score", 0.0)),
            documentation_score=float(data.get("documentation_score", 0.0)),
            test_coverage_score_estimate=float(data.get("test_coverage_score_estimate", 0.0)),
            details=details,
        )

    @property
    def quality_index(self) -> float:
        """Aggregate quality signal combining readability, docs, and coverage."""
        return (
            self.readability_score
            + self.documentation_score
            + self.test_coverage_score_estimate
        ) / 3


class CodeAnalyzer:
    """Heuristic estimation of code quality signals for all programming languages."""

    _SKIP_DIR_NAMES = {
        "__pycache__",
        ".git",
        ".github",  # GitHub workflows and configs
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
        "build",
        "dist",
        ".pytest_cache",
        ".mypy_cache",
        "target",  # Maven/Gradle
        "bin",
        "obj",  # .NET
        ".tox",
        ".nox",
        "htmlcov",
        "coverage",
        ".eggs",
        "site-packages",
    }

    # Language extensions mapping
    _LANGUAGE_EXTENSIONS = {
        ".py": "Python",
        ".java": "Java",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "React JSX",
        ".tsx": "React TSX",
        ".cpp": "C++",
        ".c": "C",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".r": "R",
        ".m": "Objective-C",
        ".dart": "Dart",
        ".lua": "Lua",
        ".pl": "Perl",
        ".sh": "Shell Script",
        ".sql": "SQL",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".vue": "Vue",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".xml": "XML",
        ".md": "Markdown",
    }

    def __init__(self, gemini_api_key: str | None = None, gemini_model: str = "models/gemini-2.0-flash-lite"):
        """Initialize code analyzer with optional Gemini AI support for all languages."""
        self._gemini_api_key = gemini_api_key
        self._gemini_model = gemini_model
        self._gemini_client = None

    def analyze(self, submission_dir: Path) -> CodeAnalysisResult:
        code_dir = submission_dir / "code"
        
        # Detect all code files (any language)
        code_files = []
        python_files = []
        
        if code_dir.exists():
            code_files = list(self._iter_code_files(code_dir))
            python_files = [f for f in code_files if f.suffix == ".py"]

        discovered_dir: Optional[Path] = None
        if not code_files:
            discovered_dir = self._discover_code_directory(submission_dir)
            if discovered_dir is not None:
                code_dir = discovered_dir
                code_files = list(self._iter_code_files(code_dir))
                python_files = [f for f in code_files if f.suffix == ".py"]

        if not code_files:
            return CodeAnalysisResult(0.0, 0.0, 0.0)
        
        # Analyze language distribution
        language_stats = self._analyze_languages(code_files)

        readability_signals: List[float] = []
        details: Dict[str, Any] = {
            "total_files": len(code_files),
            "languages": language_stats,
            "evaluated_files": [str(path.relative_to(code_dir)) for path in code_files[:20]],  # Show first 20
            "python_files_count": len(python_files),
        }
        try:
            rel_code_root = code_dir.relative_to(submission_dir)
            details["code_root"] = str(rel_code_root) or "."
        except ValueError:
            details["code_root"] = str(code_dir)
        if discovered_dir is not None:
            details["discovered_code_root"] = True

        # Run Python-specific analysis if Python files exist
        # Pylint disabled to avoid CI conflicts
        lint_details = {"status": "disabled", "reason": "Pylint analysis disabled"}
        details["lint"] = lint_details

        complexity_score, complexity_details = self._compute_complexity(python_files) if python_files else (None, {"status": "skipped", "reason": "No Python files"})
        if complexity_score is not None:
            readability_signals.append(complexity_score)
        details["complexity"] = complexity_details

        doc_ratio, doc_details = self._docstring_ratio(python_files) if python_files else (0.0, {"status": "skipped", "reason": "No Python files"})
        details["documentation"] = doc_details

        pytest_score, pytest_details = self._run_pytest(code_dir) if python_files else (None, {"status": "skipped", "reason": "No Python files"})
        details["pytest"] = pytest_details

        # Calculate readability based on available signals
        if readability_signals:
            readability = sum(readability_signals) / len(readability_signals)
            # Boost readability for multi-language projects with decent organization
            if not python_files or len(language_stats.get("languages", [])) > 1:
                # Add baseline for organized multi-language projects
                readability = max(readability, 0.4 + min(0.4, len(code_files) / 25))
        else:
            # Estimate based on file count and structure
            readability = 0.3 + min(0.7, len(code_files) / 30)

        # Calculate documentation score
        documentation = doc_ratio
        if documentation == 0.0:
            if python_files:
                # For Python projects with no docstrings, check if there's a README or comments
                has_readme = any(f.name.lower() == "readme.md" for f in code_files)
                docstrings = doc_details.get("docstrings", 0)
                max_possible = max(1, len(python_files) * 2)
                documentation = min(1.0, docstrings / max_possible)
                # Small boost for having a README
                if has_readme and documentation < 0.3:
                    documentation = 0.3
            else:
                # Estimate for non-Python projects based on file organization and README
                has_readme = any(f.name.lower() == "readme.md" for f in code_files)
                documentation = (0.5 if has_readme else 0.35) if len(code_files) > 5 else 0.25

        if pytest_score is not None:
            coverage_estimate = pytest_score
        else:
            if python_files:
                docstrings = doc_details.get("docstrings", 0)
                coverage_estimate = min(1.0, (len(python_files) + docstrings) / 50)
            else:
                # Estimate for non-Python projects
                coverage_estimate = 0.3 if len(code_files) > 10 else 0.2

        # Generate Gemini-powered code insights for ALL languages
        gemini_insights = self._generate_code_insights_with_gemini(
            code_files, python_files, language_stats, lint_details, complexity_details, doc_details
        )
        if gemini_insights:
            details["gemini_insights"] = gemini_insights

        return CodeAnalysisResult(
            readability_score=round(readability, 3),
            documentation_score=round(documentation, 3),
            test_coverage_score_estimate=round(coverage_estimate, 3),
            details=details,
        )

    def _iter_python_files(self, root: Path) -> Iterable[Path]:
        for path in root.rglob("*.py"):
            if any(part in self._SKIP_DIR_NAMES for part in path.parts):
                continue
            yield path

    def _iter_code_files(self, root: Path) -> Iterable[Path]:
        """Iterate over all recognized code files in any language."""
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in self._SKIP_DIR_NAMES for part in path.parts):
                continue
            # Check if it's a recognized code file
            if path.suffix in self._LANGUAGE_EXTENSIONS:
                yield path

    def _analyze_languages(self, code_files: List[Path]) -> Dict[str, Any]:
        """Analyze language distribution in the codebase."""
        language_counts: Dict[str, int] = {}
        language_lines: Dict[str, int] = {}
        
        for file_path in code_files:
            lang = self._LANGUAGE_EXTENSIONS.get(file_path.suffix, "Other")
            language_counts[lang] = language_counts.get(lang, 0) + 1
            
            # Try to count lines for better analysis
            try:
                lines = len(file_path.read_text(encoding='utf-8', errors='ignore').splitlines())
                language_lines[lang] = language_lines.get(lang, 0) + lines
            except Exception:
                pass
        
        # Calculate percentages
        total_files = len(code_files)
        total_lines = sum(language_lines.values()) if language_lines else 0
        
        language_info = []
        for lang in sorted(language_counts.keys(), key=lambda x: language_counts[x], reverse=True):
            info = {
                "language": lang,
                "file_count": language_counts[lang],
                "file_percentage": round(100 * language_counts[lang] / total_files, 1) if total_files > 0 else 0,
            }
            if lang in language_lines and total_lines > 0:
                info["line_count"] = language_lines[lang]
                info["line_percentage"] = round(100 * language_lines[lang] / total_lines, 1)
            language_info.append(info)
        
        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "languages": language_info,
            "primary_language": language_info[0]["language"] if language_info else "Unknown",
        }

    def _discover_code_directory(self, submission_dir: Path) -> Optional[Path]:
        # Use all code files, not just Python
        code_files = [path for path in self._iter_code_files(submission_dir)]
        if not code_files:
            return None

        top_level = [path for path in code_files if path.parent == submission_dir]
        if top_level:
            return submission_dir

        scores: Dict[Path, int] = {}
        for file_path in code_files:
            parent = file_path.parent
            while parent != submission_dir and parent.is_relative_to(submission_dir):
                try:
                    relative_parts = parent.relative_to(submission_dir).parts
                except ValueError:
                    break
                if any(part in self._SKIP_DIR_NAMES for part in relative_parts):
                    break
                scores[parent] = scores.get(parent, 0) + 1
                parent = parent.parent

        if not scores:
            return submission_dir

        def _score(entry: Tuple[Path, int]) -> Tuple[int, int, int]:
            directory, count = entry
            try:
                relative = directory.relative_to(submission_dir)
                depth = len(relative.parts)
                name = directory.name.lower()
            except ValueError:
                depth = 0
                name = directory.name.lower()

            bonus = 0
            if name in {"code", "src", "source"}:
                bonus += 5
            elif name in {"app", "backend", "server", "service"}:
                bonus += 3
            if name.startswith("test"):
                bonus -= 5

            return (count * 10 + bonus, -depth, -len(name))

        best_dir = max(scores.items(), key=_score)[0]
        return best_dir

    # ------------------------------------------------------------------
    # Linting / complexity / documentation utilities
    def _run_pylint(
        self, code_dir: Path, python_files: Iterable[Path]
    ) -> Tuple[Optional[float], Mapping[str, Any]]:
        # Validate that all files are within code_dir to prevent analyzing outside files
        code_dir_resolved = code_dir.resolve()
        validated_files = []
        for path in python_files:
            try:
                path_resolved = path.resolve()
                # Only include files that are actually within the code directory
                if path_resolved.is_relative_to(code_dir_resolved):
                    validated_files.append(str(path_resolved))
                else:
                    LOGGER.warning("Skipping file outside code directory: %s", path)
            except (ValueError, OSError) as e:
                LOGGER.debug("Failed to validate path %s: %s", path, e)
                continue
        
        if not validated_files or PylintRun is None or CollectingReporter is None:
            return None, {"status": "skipped", "reason": "pylint not available or no valid files"}

        reporter = CollectingReporter()
        args = [*validated_files, "--score=y", "--reports=n"]
        with self._cwd(code_dir):
            try:  # pragma: no cover - heavy external call
                run = PylintRun(args, reporter=reporter, do_exit=False)
            except (OSError, RuntimeError) as exc:  # pragma: no cover
                LOGGER.debug("pylint execution failed: %s", exc)
                return None, {"status": "error", "error": str(exc)}

        score = None
        if hasattr(run, "linter"):
            stats = getattr(run.linter, "stats", None)
            score = getattr(stats, "global_note", None) if stats is not None else None
        normalized = None
        if isinstance(score, (int, float)):
            normalized = max(0.0, min(1.0, score / 10.0))

        messages = [
            {
                "path": msg.path,
                "line": msg.line,
                "symbol": msg.symbol,
                "message": msg.msg or msg.message,
                "category": msg.category,
            }
            for msg in reporter.messages
        ]

        return normalized, {
            "status": "ok",
            "raw_score": score,
            "normalized_score": normalized,
            "messages": messages,
        }

    def _compute_complexity(
        self, python_files: Iterable[Path]
    ) -> Tuple[Optional[float], Mapping[str, Any]]:
        if cc_visit is None:
            return None, {"status": "skipped", "reason": "radon not available"}

        complexities: List[float] = []
        file_stats: List[Dict[str, Any]] = []

        for path in python_files:
            try:
                # Resolve path to ensure it's valid and within expected bounds
                path = path.resolve()
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            try:
                blocks = cc_visit(text)
            except (ValueError, RuntimeError) as exc:  # pragma: no cover
                LOGGER.debug("radon failed for %s: %s", path, exc)
                continue
            for block in blocks:
                complexities.append(block.complexity)
            file_stats.append(
                {
                    "path": str(path),
                    "max_complexity": max((block.complexity for block in blocks), default=0.0),
                    "average_complexity": (
                        sum(block.complexity for block in blocks) / len(blocks)
                        if blocks
                        else 0.0
                    ),
                }
            )

        if not complexities:
            return None, {"status": "skipped", "reason": "no analyzable blocks"}

        avg_complexity = sum(complexities) / len(complexities)
        penalty = max(0.0, avg_complexity - 1.0)
        normalized = max(0.0, min(1.0, 1.0 - penalty / 9.0))

        return normalized, {
            "status": "ok",
            "average_complexity": avg_complexity,
            "normalized_score": normalized,
            "files": file_stats,
        }

    def _docstring_ratio(self, python_files: Iterable[Path]) -> Tuple[float, Mapping[str, Any]]:
        documented = 0
        total = 0
        errors: List[str] = []

        for path in python_files:
            try:
                text = path.read_text(encoding="utf-8")
                tree = ast.parse(text)
            except (OSError, SyntaxError) as exc:
                errors.append(f"{path.name}: {exc}")
                continue

            total += 1  # module docstring opportunity
            if ast.get_docstring(tree):
                documented += 1

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    total += 1
                    if ast.get_docstring(node):
                        documented += 1

        ratio = documented / total if total else 0.0
        return round(ratio, 3), {
            "status": "ok",
            "objects": total,
            "docstrings": documented,
            "ratio": ratio,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Pytest integration
    def _run_pytest(self, code_dir: Path) -> Tuple[Optional[float], Mapping[str, Any]]:
        tests_dir = code_dir / "tests"
        if not tests_dir.exists():
            return None, {"status": "skipped", "reason": "no tests directory"}

        cmd = [sys.executable, "-m", "pytest", "-q", "--maxfail=1"]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(code_dir),
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return 0.0, {
                "status": "timeout",
                "command": " ".join(cmd),
            }

        output = (proc.stdout or "") + (proc.stderr or "")
        trimmed_output = output[-4000:]
        passed = proc.returncode == 0

        return (1.0 if passed else 0.0), {
            "status": "passed" if passed else "failed",
            "command": " ".join(cmd),
            "returncode": proc.returncode,
            "output": trimmed_output,
        }

    # ------------------------------------------------------------------
    @contextlib.contextmanager
    def _cwd(self, path: Path):
        current = Path.cwd()
        try:
            os.chdir(path)
            yield
        finally:
            os.chdir(current)

    def _generate_code_insights_with_gemini(
        self,
        code_files: List[Path],
        python_files: List[Path],
        language_stats: Dict[str, Any],
        lint_details: Mapping[str, Any],
        complexity_details: Mapping[str, Any],
        doc_details: Mapping[str, Any]
    ) -> Dict[str, Any] | None:
        """Generate AI-powered code insights and suggestions using Gemini for ALL languages."""
        if not self._gemini_api_key or not genai:
            return None

        try:
            # Initialize Gemini client if needed
            if self._gemini_client is None:
                genai.configure(api_key=self._gemini_api_key)
                self._gemini_client = genai.GenerativeModel(self._gemini_model)

            # Prepare language distribution
            primary_language = language_stats.get("primary_language", "Unknown")
            total_files = language_stats.get("total_files", 0)
            total_lines = language_stats.get("total_lines", 0)
            languages_list = language_stats.get("languages", [])
            
            # Build language breakdown
            lang_breakdown = "\n".join([
                f"- {lang['language']}: {lang['file_count']} files ({lang['file_percentage']}%)" +
                (f", {lang.get('line_count', 0)} lines ({lang.get('line_percentage', 0)}%)" if 'line_count' in lang else "")
                for lang in languages_list[:5]  # Top 5 languages
            ])
            
            # Prepare Python-specific metrics if available
            lint_messages = lint_details.get("messages", [])[:10]
            lint_status = lint_details.get("status", "unknown")
            lint_score = lint_details.get("normalized_score")
            
            complexity_score = complexity_details.get("normalized_score")
            avg_complexity = complexity_details.get("average_complexity")
            
            doc_ratio = doc_details.get("ratio", 0.0)
            total_functions = doc_details.get("total_functions", 0)
            
            # Build context for Gemini
            context = f"""Multi-Language Code Quality Analysis:

Primary Language: {primary_language}
Total Files: {total_files}
Total Lines: {total_lines:,} (estimated)

Language Breakdown:
{lang_breakdown}

"""

            # Add Python-specific metrics if available
            if python_files:
                context += f"""
Python-Specific Analysis:
Files Analyzed: {len(python_files)} Python files

Linting Status: {lint_status}
{f"Lint Score: {lint_score:.3f}/1.0" if lint_score is not None else "Lint Score: N/A"}

Complexity Score: {f"{complexity_score:.3f}/1.0" if complexity_score else "N/A"}
{f"Average Complexity: {avg_complexity:.2f}" if avg_complexity else ""}

Documentation Ratio: {doc_ratio:.3f}
Total Functions: {total_functions}

"""

            # Add lint messages if available (limit to avoid context overflow)
            if lint_messages:
                context += "Top Linting Issues (Python):\n"
                for msg in lint_messages[:5]:  # Limit to 5 messages to prevent context overflow
                    # Truncate long paths to keep context manageable
                    path_str = str(msg.get('path', 'unknown'))
                    if len(path_str) > 60:
                        path_str = "..." + path_str[-57:]
                    context += f"- [{msg.get('symbol')}] {path_str}:{msg.get('line')} - {msg.get('message', '')[:100]}\n"
            elif python_files:
                context += "Linting Issues: None detected\n"
            
            context += "\n"
            
            # Safety check: truncate context if too large (Gemini has ~30K token limit, roughly 120K chars)
            max_context_chars = 8000  # Leave room for prompt and response
            if len(context) > max_context_chars:
                LOGGER.warning("Context too large (%d chars), truncating to %d chars", len(context), max_context_chars)
                context = context[:max_context_chars] + "\n\n[Context truncated due to size...]"

            prompt = f"""{context}

Based on this multi-language code analysis, provide:
1. **Overall Assessment** (2-3 sentences): Summarize the code quality, language choices, and what stands out
2. **Strengths** (2-3 bullet points): What the codebase does well (consider all languages)
3. **Improvement Suggestions** (3-4 actionable bullet points): Specific recommendations for the primary language ({primary_language}) and overall project structure
4. **Priority Fix** (if issues exist): The most important improvement to make first

Be concise, specific, and constructive. Tailor advice to the {primary_language} ecosystem and best practices."""

            LOGGER.info("Generating Gemini code insights (context: %d chars, prompt: %d chars)", len(context), len(prompt))

            response = self._gemini_client.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.5,  # Balanced for code analysis
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 600,
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )

            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                # Check if content was blocked
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = str(candidate.finish_reason)
                    if 'SAFETY' in finish_reason or 'BLOCKED' in finish_reason:
                        LOGGER.warning("Gemini response blocked due to safety filters: %s", finish_reason)
                        return None
                    if 'RECITATION' in finish_reason:
                        LOGGER.warning("Gemini response blocked due to recitation: %s", finish_reason)
                        return None
                
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                    if candidate.content.parts:
                        insights_text = candidate.content.parts[0].text.strip()
                        LOGGER.info("✓ Generated Gemini code insights (%d chars)", len(insights_text))
                        return {
                            "analysis": insights_text,
                            "generated_by": self._gemini_model
                        }
                else:
                    LOGGER.warning("Gemini response has no content parts")
            else:
                LOGGER.warning("Gemini response has no candidates")

        except Exception as exc:
            LOGGER.error("Gemini code insights generation failed: %s", exc, exc_info=True)

        return None
