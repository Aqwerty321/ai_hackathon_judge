from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodeAnalysisResult:
    """Metrics summarising code quality aspects."""

    readability_score: float
    documentation_score: float
    test_coverage_score_estimate: float

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

    def analyze(self, submission_dir: Path) -> CodeAnalysisResult:
        code_dir = submission_dir / "code"
        if not code_dir.exists():
            return CodeAnalysisResult(0.0, 0.0, 0.0)

        python_files = list(code_dir.rglob("*.py"))
        file_count = len(python_files)
        docstring_count = sum(self._count_docstrings(path) for path in python_files)

        readability = 0.3 + min(0.7, file_count / 20)
        documentation = min(1.0, docstring_count / max(1, file_count * 2))
        coverage_estimate = min(1.0, (file_count + docstring_count) / 50)

        return CodeAnalysisResult(
            readability_score=round(readability, 3),
            documentation_score=round(documentation, 3),
            test_coverage_score_estimate=round(coverage_estimate, 3),
        )

    def _count_docstrings(self, path: Path) -> int:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return 0
        triple_double = text.count("\"\"\"") // 2
        triple_single = text.count("'''") // 2
        return triple_double + triple_single
