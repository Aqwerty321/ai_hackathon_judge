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
    text_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    text_similarity_top_k: int = 5
    text_ai_detector_model: str = "roberta-base-openai-detector"
    text_llm_model_path: Path | None = Path("models") / "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    text_llm_model_type: str = "auto"
    text_llm_max_tokens: int = 256
    text_llm_context_length: int = 8192
    text_llm_gpu_layers: int | None = None
    text_ai_detector_context_length: int = 8192
    device_preference: str = "auto"

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

    @property
    def text_cache_dir(self) -> Path:
        return (self.base_dir / self.intermediate_dir / "text").resolve()

    @property
    def resolved_text_llm_model_path(self) -> Path | None:
        if self.text_llm_model_path is None:
            return None
        path = Path(self.text_llm_model_path)
        if not path.is_absolute():
            path = (self.base_dir / path).resolve()
        return path

    @property
    def analysis_cache_dir(self) -> Path:
        return (self.base_dir / self.intermediate_dir / "analysis_cache").resolve()

    @property
    def extracted_submissions_dir(self) -> Path:
        return (self.base_dir / self.intermediate_dir / "extracted_submissions").resolve()
