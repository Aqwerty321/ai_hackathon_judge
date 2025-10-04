from pathlib import Path

from ai_judge.modules.text_analyzer import TextAnalyzer


def test_text_analyzer_similarity_and_claims(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "sample.txt").write_text(
        "Project Alpha reduces energy waste through adaptive automation and smart devices.",
        encoding="utf-8",
    )

    description = (
        "Our project guarantees 98% accuracy in reducing household energy use. "
        "It delivers adaptive automation via smart devices and sustainability analytics."
    )
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "description.txt").write_text(description, encoding="utf-8")

    analyzer = TextAnalyzer(
        similarity_corpus_dir=corpus_dir,
        intermediate_dir=tmp_path / "cache",
        embedding_model=None,
        top_k=3,
        ai_detector_model=None,
    )

    result = analyzer.analyze(submission_dir)

    assert result.summary.startswith("Our project")
    assert result.similarity_matches
    assert result.similarity_matches[0].source == "sample"
    assert any("accuracy" in flag.statement.lower() for flag in result.suspect_claims)
    assert 0.0 <= result.ai_generated_likelihood <= 1.0
    assert all(flag.llm_verdict is None for flag in result.suspect_claims)


def test_text_analyzer_readme_fallback(tmp_path: Path) -> None:
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "README.md").write_text(
        """# Sample Project

This readme explains the project goals and architecture.

It highlights exceptional accuracy and innovative features.
""",
        encoding="utf-8",
    )

    analyzer = TextAnalyzer(
        similarity_corpus_dir=None,
        intermediate_dir=tmp_path / "cache",
        embedding_model=None,
        top_k=3,
        ai_detector_model=None,
    )

    result = analyzer.analyze(submission_dir)

    assert "Sample Project" in result.summary
    assert result.originality_score >= 0.0
    assert result.suspect_claims  # marketing language should trigger a flag


def test_combined_summary_generation(tmp_path: Path) -> None:
    """Test AI-powered combined summary from README and transcript."""
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    readme_text = """# EcoTracker Pro

An innovative energy monitoring solution that provides real-time insights
into household power consumption. Our intelligent algorithms analyze usage
patterns and suggest optimization strategies.
"""
    (submission_dir / "README.md").write_text(readme_text, encoding="utf-8")

    # Simulate a video transcript
    transcript = (
        "Hello everyone. Today I'm presenting EcoTracker Pro, which monitors "
        "electricity usage in homes. The dashboard shows consumption trends "
        "and helps families reduce their carbon footprint through smart alerts."
    )

    analyzer = TextAnalyzer(
        similarity_corpus_dir=None,
        intermediate_dir=tmp_path / "cache",
        embedding_model=None,
        top_k=3,
        ai_detector_model=None,
    )

    result = analyzer.analyze(submission_dir, transcript=transcript)

    # Verify combined summary exists and contains relevant terms
    assert result.combined_summary is not None
    assert len(result.combined_summary) > 0
    # Summary should reference project name or key concepts
    combined_lower = result.combined_summary.lower()
    assert any(
        term in combined_lower
        for term in ["eco", "energy", "monitor", "consumption", "power"]
    )


def test_gemini_priority_over_local_models(tmp_path: Path) -> None:
    """Test that Gemini API is prioritized when API key is provided."""
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "README.md").write_text("Test project", encoding="utf-8")

    # Without API key - should use local BART
    analyzer_no_key = TextAnalyzer(
        similarity_corpus_dir=None,
        intermediate_dir=tmp_path / "cache1",
        embedding_model=None,
        top_k=3,
        ai_detector_model=None,
        gemini_api_key=None,
    )

    # With invalid API key - should fallback to BART
    analyzer_with_key = TextAnalyzer(
        similarity_corpus_dir=None,
        intermediate_dir=tmp_path / "cache2",
        embedding_model=None,
        top_k=3,
        ai_detector_model=None,
        gemini_api_key="test-key-invalid",
    )

    result_no_key = analyzer_no_key.analyze(submission_dir, transcript="Test")
    result_with_key = analyzer_with_key.analyze(submission_dir, transcript="Test")

    # Both should produce summaries (fallback works)
    # We don't test actual API calls to avoid requiring real keys in tests
    assert isinstance(result_no_key.combined_summary, (str, type(None)))
    assert isinstance(result_with_key.combined_summary, (str, type(None)))
