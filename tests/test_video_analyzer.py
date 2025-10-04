from pathlib import Path

from ai_judge.modules.video_analyzer import VideoAnalyzer


def test_video_analyzer_reads_transcript(tmp_path: Path) -> None:
    transcript = tmp_path / "presentation_transcript.txt"
    transcript.write_text("Hello world. Welcome to the demo!", encoding="utf-8")

    cache_dir = tmp_path / "cache"
    analyzer = VideoAnalyzer(intermediate_dir=cache_dir)
    result = analyzer.analyze(tmp_path)

    assert "Hello world" in result.transcript
    assert 0.0 <= result.clarity_score <= 1.0
    assert result.estimated_duration_seconds >= 30.0
    assert result.transcription_source == "submission_transcript"
    assert result.sentiment_label in {"positive", "negative", "neutral"}
    assert 0.0 <= result.sentiment_score <= 1.0


def test_video_analyzer_description_fallback(tmp_path: Path) -> None:
    description = tmp_path / "description.txt"
    description.write_text(
        "This project delivers great innovation and positive impact.",
        encoding="utf-8",
    )

    analyzer = VideoAnalyzer(intermediate_dir=tmp_path / "cache")
    result = analyzer.analyze(tmp_path)

    assert "innovation" in result.transcript
    assert result.transcription_source == "description_fallback"
    assert result.sentiment_label in {"positive", "negative", "neutral"}


def test_video_analyzer_readme_fallback(tmp_path: Path) -> None:
    submission_dir = tmp_path
    (submission_dir / "README.md").write_text(
        "Project overview: zero bugs guarantee.",
        encoding="utf-8",
    )

    analyzer = VideoAnalyzer(intermediate_dir=submission_dir / "cache")
    result = analyzer.analyze(submission_dir)

    assert "project overview" in result.transcript.lower()
    assert result.transcription_source == "readme_fallback"
    assert result.sentiment_label in {"positive", "negative", "neutral"}
