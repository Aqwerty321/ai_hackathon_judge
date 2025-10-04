from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .scoring.criteria import JudgingCriteria


@dataclass(slots=True)
class Config:
    """Runtime configuration for the judging pipeline."""

    base_dir: Path = Path(".")
    data_dir: Path = Path("data")
    reports_dir: Path = Path("reports")
    models_dir: Path = Path("models")
    intermediate_dir: Path = Path("data") / "intermediate_outputs"
    similarity_corpus_dir: Path = Path("data") / "similarity_corpus"
    default_submission_name: str = "project_alpha"
    criteria_path: Path = Path("config") / "judging_criteria.json"
    video_transcription_model: str = "base"
    video_sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english"

    def submission_dir(self, name: str | None = None) -> Path:
        target = Path(self.data_dir) / "submissions" / (name or self.default_submission_name)
        return (self.base_dir / target).resolve()

    @property
    def default_submission_dir(self) -> Path:
        return self.submission_dir()

    def load_criteria(self) -> JudgingCriteria:
        criteria_file = (self.base_dir / self.criteria_path).resolve()
        if criteria_file.exists():
            return JudgingCriteria.from_json(criteria_file)
        return JudgingCriteria.default()

    @property
    def transcript_cache_dir(self) -> Path:
        return (self.base_dir / self.intermediate_dir / "transcripts").resolve()
