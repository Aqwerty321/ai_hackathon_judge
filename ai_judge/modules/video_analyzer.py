from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..utils.file_helpers import read_text


@dataclass(frozen=True)
class VideoAnalysisResult:
    """Lightweight representation of the video analysis stage."""

    transcript: str
    clarity_score: float
    estimated_duration_seconds: float


class VideoAnalyzer:
    """Simple heuristic-based analyzer for project videos."""

    def __init__(self, transcript_fallback: Iterable[str] | None = None) -> None:
        self._fallback_lines = list(transcript_fallback or ())

    def analyze(self, submission_dir: Path) -> VideoAnalysisResult:
        transcript_path = submission_dir / "presentation_transcript.txt"
        transcript = read_text(transcript_path)

        if not transcript.strip():
            raw_fallback = read_text(submission_dir / "description.txt")
            transcript = (
                raw_fallback
                if raw_fallback.strip()
                else "\n".join(self._fallback_lines) or "No transcript available."
            )

        clarity = self._estimate_clarity(transcript)
        duration = max(len(transcript.split()) / 2.5, 30.0)
        return VideoAnalysisResult(
            transcript=transcript.strip(),
            clarity_score=clarity,
            estimated_duration_seconds=duration,
        )

    def _estimate_clarity(self, transcript: str) -> float:
        if not transcript.strip():
            return 0.0
        sentences = transcript.count(".") + transcript.count("!") + transcript.count("?")
        clarity = min(1.0, max(0.3, sentences / max(1, len(transcript.split()) / 15)))
        return round(clarity, 3)
