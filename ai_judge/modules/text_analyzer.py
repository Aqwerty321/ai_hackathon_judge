from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from ..utils.file_helpers import read_text


@dataclass(frozen=True)
class TextAnalysisResult:
    """Results of analyzing the written project description."""

    originality_score: float
    feasibility_score: float
    summary: str


class TextAnalyzer:
    """Rule-based text analyzer for project submissions."""

    def __init__(self, similarity_corpus_dir: Path | None = None) -> None:
        self.similarity_corpus_dir = similarity_corpus_dir

    def analyze(self, submission_dir: Path) -> TextAnalysisResult:
        description = read_text(submission_dir / "description.txt")
        word_count = len(description.split())
        originality = self._estimate_originality(description)
        feasibility = self._estimate_feasibility(word_count)
        summary = self._summarize(description)
        return TextAnalysisResult(
            originality_score=originality,
            feasibility_score=feasibility,
            summary=summary,
        )

    def _estimate_originality(self, description: str) -> float:
        if not description.strip():
            return 0.0
        tokens = description.split()
        unique_tokens = len({token.lower() for token in tokens})
        return round(unique_tokens / len(tokens), 3) if tokens else 0.0

    def _estimate_feasibility(self, word_count: int) -> float:
        if word_count == 0:
            return 0.0
        return round(min(1.0, math.log(word_count + 1, 10)), 3)

    def _summarize(self, description: str, max_words: int = 40) -> str:
        if not description:
            return "No project description provided."
        tokens = description.split()
        if len(tokens) <= max_words:
            return description.strip()
        return " ".join(tokens[:max_words]) + "..."
