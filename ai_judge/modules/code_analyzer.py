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
    """Heuristic estimation of code quality signals."""

    _SKIP_DIR_NAMES = {
        "__pycache__",
        ".git",
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
        "build",
        "dist",
        ".pytest_cache",
        ".mypy_cache",
    }

    def analyze(self, submission_dir: Path) -> CodeAnalysisResult:
        code_dir = submission_dir / "code"
        python_files = []
        if code_dir.exists():
            python_files = list(self._iter_python_files(code_dir))

        discovered_dir: Optional[Path] = None
        if not python_files:
            discovered_dir = self._discover_code_directory(submission_dir)
            if discovered_dir is not None:
                code_dir = discovered_dir
                python_files = list(self._iter_python_files(code_dir))

        if not python_files:
            return CodeAnalysisResult(0.0, 0.0, 0.0)

        readability_signals: List[float] = []
        details: Dict[str, Any] = {
            "evaluated_files": [str(path.relative_to(code_dir)) for path in python_files],
        }
        try:
            rel_code_root = code_dir.relative_to(submission_dir)
            details["code_root"] = str(rel_code_root) or "."
        except ValueError:
            details["code_root"] = str(code_dir)
        if discovered_dir is not None:
            details["discovered_code_root"] = True

        lint_score, lint_details = self._run_pylint(code_dir, python_files)
        if lint_score is not None:
            readability_signals.append(lint_score)
        details["lint"] = lint_details

        complexity_score, complexity_details = self._compute_complexity(python_files)
        if complexity_score is not None:
            readability_signals.append(complexity_score)
        details["complexity"] = complexity_details

        doc_ratio, doc_details = self._docstring_ratio(python_files)
        details["documentation"] = doc_details

        pytest_score, pytest_details = self._run_pytest(code_dir)
        details["pytest"] = pytest_details

        if readability_signals:
            readability = sum(readability_signals) / len(readability_signals)
        else:
            readability = 0.3 + min(0.7, len(python_files) / 20)

        documentation = doc_ratio
        if documentation == 0.0:
            docstrings = doc_details.get("docstrings", 0)
            max_possible = max(1, len(python_files) * 2)
            documentation = min(1.0, docstrings / max_possible)

        if pytest_score is not None:
            coverage_estimate = pytest_score
        else:
            docstrings = doc_details.get("docstrings", 0)
            coverage_estimate = min(1.0, (len(python_files) + docstrings) / 50)

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

    def _discover_code_directory(self, submission_dir: Path) -> Optional[Path]:
        python_files = [path for path in self._iter_python_files(submission_dir)]
        if not python_files:
            return None

        top_level = [path for path in python_files if path.parent == submission_dir]
        if top_level:
            return submission_dir

        scores: Dict[Path, int] = {}
        for file_path in python_files:
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
        files = [str(path) for path in python_files]
        if not files or PylintRun is None or CollectingReporter is None:
            return None, {"status": "skipped", "reason": "pylint not available"}

        reporter = CollectingReporter()
        args = [*files, "--score=y", "--reports=n"]
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
