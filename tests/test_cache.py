from pathlib import Path

from ai_judge.modules.video_analyzer import VideoAnalysisResult
from ai_judge.utils.cache import AnalysisCache
from ai_judge.utils.fingerprint import directory_fingerprint


def test_analysis_cache_roundtrip(tmp_path: Path) -> None:
    cache = AnalysisCache(tmp_path)
    payload = {"value": 42}

    cache.store("alpha", "video", "sig-1", payload)
    assert cache.load("alpha", "video", "sig-1") == payload
    assert cache.load("alpha", "video", "sig-2") is None

    video = VideoAnalysisResult(
        transcript="Hello world",
        clarity_score=0.8,
        estimated_duration_seconds=120.0,
        sentiment_label="positive",
        sentiment_score=0.9,
        transcription_source="unit",
    )
    cache.store("alpha", "video", "sig-3", video)
    cached_dict = cache.load("alpha", "video", "sig-3")
    assert isinstance(cached_dict, dict)
    assert cached_dict["transcript"] == "Hello world"


def test_directory_fingerprint_changes_on_update(tmp_path: Path) -> None:
    file_path = tmp_path / "artifact.txt"
    file_path.write_text("before", encoding="utf-8")
    first = directory_fingerprint(tmp_path)

    file_path.write_text("after", encoding="utf-8")
    second = directory_fingerprint(tmp_path)

    assert first != second
