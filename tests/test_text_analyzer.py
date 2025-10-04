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
