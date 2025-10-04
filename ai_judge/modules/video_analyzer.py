from __future__ import annotations

import hashlib
import logging
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Mapping, Tuple

from ..utils.file_helpers import ensure_directory, read_text

try:  # pragma: no cover - optional heavy dependency
    import whisper
except ImportError:  # pragma: no cover - optional heavy dependency
    whisper = None

try:  # pragma: no cover - optional heavy dependency
    from moviepy.editor import VideoFileClip  # type: ignore
except ImportError:  # pragma: no cover - optional heavy dependency
    VideoFileClip = None  # type: ignore

try:  # pragma: no cover - optional heavy dependency
    from transformers import pipeline  # type: ignore
except ImportError:  # pragma: no cover - optional heavy dependency
    pipeline = None  # type: ignore


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VideoAnalysisResult:
    """Lightweight representation of the video analysis stage."""

    transcript: str
    clarity_score: float
    estimated_duration_seconds: float
    sentiment_label: str
    sentiment_score: float
    transcription_source: str

    def to_dict(self) -> dict[str, object]:
        return dict(asdict(self))

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "VideoAnalysisResult":
        return cls(
            transcript=str(data.get("transcript", "")),
            clarity_score=float(data.get("clarity_score", 0.0)),
            estimated_duration_seconds=float(data.get("estimated_duration_seconds", 0.0)),
            sentiment_label=str(data.get("sentiment_label", "neutral")),
            sentiment_score=float(data.get("sentiment_score", 0.0)),
            transcription_source=str(data.get("transcription_source", "unknown")),
        )


class VideoAnalyzer:
    """Hybrid video analyzer with transcription, sentiment, and heuristics."""

    def __init__(
        self,
        transcript_fallback: Iterable[str] | None = None,
        intermediate_dir: Path | None = None,
        transcription_model: str = "base",
        sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english",
    ) -> None:
        self._fallback_lines = list(transcript_fallback or ())
        self._cache_dir = Path(intermediate_dir) if intermediate_dir else None
        if self._cache_dir:
            ensure_directory(self._cache_dir)
        self._transcription_model = transcription_model
        self._sentiment_model = sentiment_model
        self._sentiment_pipeline = None

    def analyze(self, submission_dir: Path) -> VideoAnalysisResult:
        transcript_path = submission_dir / "presentation_transcript.txt"
        transcript, source = self._load_transcript(submission_dir, transcript_path)

        if not transcript.strip():
            raw_fallback = read_text(submission_dir / "description.txt")
            if raw_fallback.strip():
                transcript = raw_fallback
                source = "description_fallback"
            else:
                transcript = "\n".join(self._fallback_lines) or "No transcript available."
                source = "manual_fallback"

        clarity = self._estimate_clarity(transcript)
        duration = self._estimate_duration(submission_dir / "presentation.mp4", transcript)
        sentiment_label, sentiment_score = self._analyze_sentiment(transcript)

        return VideoAnalysisResult(
            transcript=transcript.strip(),
            clarity_score=clarity,
            estimated_duration_seconds=duration,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
            transcription_source=source,
        )

    # ------------------------------------------------------------------
    # Transcript handling
    def _load_transcript(self, submission_dir: Path, transcript_path: Path) -> Tuple[str, str]:
        if transcript_path.exists():
            return read_text(transcript_path), "submission_transcript"

        cached = self._read_cached_transcript(submission_dir)
        if cached:
            return cached, "cached_transcript"

        video_path = submission_dir / "presentation.mp4"
        if video_path.exists():
            transcript = self._transcribe_video(video_path)
            if transcript:
                self._write_cached_transcript(submission_dir, transcript)
                return transcript, "whisper_transcription"

        return "", "missing_transcript"

    def _cache_path(self, submission_dir: Path) -> Path | None:
        if not self._cache_dir:
            return None
        digest = hashlib.sha1(str(submission_dir.resolve()).encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.txt"

    def _read_cached_transcript(self, submission_dir: Path) -> str | None:
        cache_path = self._cache_path(submission_dir)
        if cache_path and cache_path.exists():
            return read_text(cache_path)
        return None

    def _write_cached_transcript(self, submission_dir: Path, transcript: str) -> None:
        cache_path = self._cache_path(submission_dir)
        if not cache_path:
            return
        ensure_directory(cache_path.parent)
        cache_path.write_text(transcript, encoding="utf-8")

    def _transcribe_video(self, video_path: Path) -> str | None:
        if whisper is None:
            LOGGER.debug("Skipping transcription for %s: whisper not installed", video_path)
            return None
        if VideoFileClip is None:
            LOGGER.debug("Skipping transcription for %s: moviepy not installed", video_path)
            return None

        audio_path = None
        try:
            with VideoFileClip(str(video_path)) as clip:  # type: ignore[attr-defined]
                if clip.audio is None:
                    LOGGER.warning("Video '%s' has no audio track for transcription.", video_path)
                    return None
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    audio_path = Path(tmp.name)
                clip.audio.write_audiofile(str(audio_path), verbose=False, logger=None)

            model = whisper.load_model(self._transcription_model)
            result = model.transcribe(str(audio_path))
            transcript = result.get("text", "").strip()
            return transcript or None
        except Exception as exc:  # pragma: no cover - dependent on external libs
            LOGGER.warning("Video transcription failed for '%s': %s", video_path, exc)
            return None
        finally:
            if audio_path:
                try:
                    Path(audio_path).unlink(missing_ok=True)
                except OSError:
                    LOGGER.debug("Temporary audio file cleanup failed for %s", audio_path)

    # ------------------------------------------------------------------
    # Metrics & heuristics
    def _estimate_clarity(self, transcript: str) -> float:
        if not transcript.strip():
            return 0.0
        sentences = transcript.count(".") + transcript.count("!") + transcript.count("?")
        clarity = min(1.0, max(0.3, sentences / max(1, len(transcript.split()) / 15)))
        return round(clarity, 3)

    def _estimate_duration(self, video_path: Path, transcript: str) -> float:
        if VideoFileClip is not None and video_path.exists():
            try:  # pragma: no cover - dependent on moviepy
                with VideoFileClip(str(video_path)) as clip:  # type: ignore[attr-defined]
                    if clip.duration:
                        return round(float(clip.duration), 3)
            except Exception as exc:
                LOGGER.debug("Unable to read video duration for '%s': %s", video_path, exc)
        return max(len(transcript.split()) / 2.5, 30.0)

    def _analyze_sentiment(self, transcript: str) -> Tuple[str, float]:
        if not transcript.strip():
            return "neutral", 0.0

        if pipeline is None:
            return self._heuristic_sentiment(transcript)

        try:  # pragma: no cover - dependent on transformers
            if self._sentiment_pipeline is None:
                self._sentiment_pipeline = pipeline("sentiment-analysis", model=self._sentiment_model)
            truncated = transcript[:4096]
            result = self._sentiment_pipeline(truncated)[0]
            label = str(result.get("label", "neutral")).lower()
            score = float(result.get("score", 0.0))
            if label in {"positive", "neg", "negative", "neutral"}:
                label = label.replace("neg", "negative")
            return label, round(score, 3)
        except Exception as exc:
            LOGGER.debug("Sentiment analysis failed: %s", exc)
            return self._heuristic_sentiment(transcript)

    def _heuristic_sentiment(self, transcript: str) -> Tuple[str, float]:
        positive_words = {"great", "good", "progress", "success", "innovation"}
        negative_words = {"issue", "problem", "failure", "risk", "concern"}

        tokens = [token.strip(".,!?").lower() for token in transcript.split()]
        pos_hits = sum(token in positive_words for token in tokens)
        neg_hits = sum(token in negative_words for token in tokens)

        if pos_hits == neg_hits:
            return "neutral", 0.5
        if pos_hits > neg_hits:
            score = min(1.0, 0.6 + pos_hits / max(1, len(tokens)))
            return "positive", round(score, 3)
        score = min(1.0, 0.6 + neg_hits / max(1, len(tokens)))
        return "negative", round(score, 3)
