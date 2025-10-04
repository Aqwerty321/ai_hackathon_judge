from pathlib import Path
from textwrap import dedent

from ai_judge.modules.code_analyzer import CodeAnalyzer


def test_code_analyzer_runs_lint_complexity_and_tests(tmp_path: Path) -> None:
    code_dir = tmp_path / "code"
    tests_dir = code_dir / "tests"
    tests_dir.mkdir(parents=True)

    (code_dir / "__init__.py").write_text('"""Package init."""\n', encoding="utf-8")

    module_source = dedent(
        '''
        """Minimal application module."""

        def add(a: int, b: int) -> int:
            """Return the sum of two integers."""
            return a + b


        class Greeter:
            """Simple greeter."""

            def greet(self, name: str) -> str:
                """Return a greeting."""
                return f"Hello {name}"
        '''
    ).strip() + "\n"
    (code_dir / "app.py").write_text(module_source, encoding="utf-8")

    test_source = dedent(
        '''
        """Tests for app."""

        from app import add


        def test_add() -> None:
            assert add(2, 3) == 5
        '''
    ).strip() + "\n"
    (tests_dir / "test_app.py").write_text(test_source, encoding="utf-8")

    analyzer = CodeAnalyzer()
    result = analyzer.analyze(tmp_path)

    assert 0.0 <= result.readability_score <= 1.0
    assert 0.0 <= result.documentation_score <= 1.0
    assert 0.0 <= result.test_coverage_score_estimate <= 1.0
    assert result.details["pytest"]["status"] in {"passed", "failed", "timeout"}
    assert "evaluated_files" in result.details
    assert "lint" in result.details
    assert "complexity" in result.details
    assert "documentation" in result.details


def test_code_analyzer_returns_zero_without_code_dir(tmp_path: Path) -> None:
    analyzer = CodeAnalyzer()

    result = analyzer.analyze(tmp_path)

    assert result.readability_score == 0.0
    assert result.documentation_score == 0.0
    assert result.test_coverage_score_estimate == 0.0
    assert result.quality_index == 0.0
    assert result.details == {}


def test_code_analyzer_handles_empty_code_directory(tmp_path: Path) -> None:
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "README.md").write_text("no python here", encoding="utf-8")

    analyzer = CodeAnalyzer()
    result = analyzer.analyze(tmp_path)

    assert result.readability_score == 0.0
    assert result.documentation_score == 0.0
    assert result.test_coverage_score_estimate == 0.0
    assert result.details == {}


def test_code_analyzer_records_skipped_tools_when_dependencies_missing(tmp_path: Path, monkeypatch) -> None:
    from ai_judge.modules import code_analyzer as module

    monkeypatch.setattr(module, "PylintRun", None)
    monkeypatch.setattr(module, "CollectingReporter", None)
    monkeypatch.setattr(module, "cc_visit", None)

    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "module.py").write_text(
        """def add(a, b):\n    return a + b\n""",
        encoding="utf-8",
    )

    analyzer = CodeAnalyzer()
    result = analyzer.analyze(tmp_path)

    assert result.readability_score == 0.35
    assert result.documentation_score == 0.0
    assert result.test_coverage_score_estimate == 0.02
    assert result.details["lint"]["status"] == "skipped"
    assert result.details["complexity"]["status"] == "skipped"
    assert result.details["pytest"]["status"] == "skipped"
    assert result.details["documentation"]["docstrings"] == 0