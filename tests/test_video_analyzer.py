from pathlib import Path

from ai_judge.modules.video_analyzer import VideoAnalyzer


def test_video_analyzer_reads_transcript(tmp_path: Path) -> None:
    transcript = tmp_path / "presentation_transcript.txt"
    transcript.write_text("Hello world. Welcome to the demo!", encoding="utf-8")

    analyzer = VideoAnalyzer()
    result = analyzer.analyze(tmp_path)

    assert "Hello world" in result.transcript
    assert 0.0 <= result.clarity_score <= 1.0
    assert result.estimated_duration_seconds >= 30.0
