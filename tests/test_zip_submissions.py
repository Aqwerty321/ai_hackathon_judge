import zipfile
from pathlib import Path

from ai_judge.config import Config
from ai_judge.main import run_pipeline


def _create_sample_submission(tmp_path: Path) -> Path:
    submission_root = tmp_path / "submission"
    project_root = submission_root / "Student-Management-System-main"
    nested_code = project_root / "src" / "student_management_system"
    tests_dir = nested_code / "tests"
    tests_dir.mkdir(parents=True)

    (project_root / "README.md").write_text(
        "Student management system with nested source directory.",
        encoding="utf-8",
    )
    (nested_code / "__init__.py").write_text("", encoding="utf-8")
    (nested_code / "app.py").write_text("print('hello world')\n", encoding="utf-8")
    (tests_dir / "test_placeholder.py").write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")
    return submission_root


def test_run_pipeline_accepts_zipped_submission(tmp_path: Path) -> None:
    base_dir = tmp_path
    data_dir = base_dir / "data"
    submissions_dir = data_dir / "submissions"
    submissions_dir.mkdir(parents=True)
    (data_dir / "similarity_corpus").mkdir(parents=True)
    (base_dir / "reports").mkdir()
    (base_dir / "models").mkdir()

    submission_root = _create_sample_submission(tmp_path)
    zip_path = submissions_dir / "project_zip.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for path in submission_root.rglob("*"):
            archive.write(path, path.relative_to(submission_root))

    config = Config(
        base_dir=base_dir,
        data_dir=Path("data"),
        reports_dir=Path("reports"),
        models_dir=Path("models"),
        intermediate_dir=Path("intermediate"),
        similarity_corpus_dir=Path("data") / "similarity_corpus",
    )

    result = run_pipeline(config=config, submission_name="project_zip")

    submission_payload = result["submissions"][0]

    assert submission_payload["submission_dir"] != str(zip_path)
    extracted_dir = Path(submission_payload["submission_dir"])
    assert extracted_dir.exists()

    display_dir = submission_payload["submission_dir_display"]
    assert not Path(display_dir).is_absolute()
    source_display = submission_payload["submission_source_display"]
    assert Path(source_display) == Path("data") / "submissions" / "project_zip.zip"
    assert Path(submission_payload["submission_source"]).resolve() == zip_path.resolve()

    extracted_root = Path(submission_payload["extracted_root"])
    assert extracted_root.exists()
    assert submission_payload["normalized_from_extracted"] is True
    extracted_display_path = Path(submission_payload["extracted_root_display"])
    expected_prefix_parts = Path(config.intermediate_dir).parts
    assert extracted_display_path.parts[: len(expected_prefix_parts)] == expected_prefix_parts

    code_details = submission_payload["code_analysis"]["details"]
    code_root = Path(code_details["code_root"])
    assert code_root.parts[-1] == "src"
    assert any("student_management_system" in str(path) for path in code_details["evaluated_files"])
    assert code_details.get("discovered_code_root") is True

    report_path = Path(submission_payload["report_path"])
    assert report_path.exists()


def test_run_pipeline_skip_cache_recomputes(tmp_path: Path) -> None:
    base_dir = tmp_path
    data_dir = base_dir / "data"
    submissions_dir = data_dir / "submissions"
    submissions_dir.mkdir(parents=True)
    (data_dir / "similarity_corpus").mkdir(parents=True)
    (base_dir / "reports").mkdir()
    (base_dir / "models").mkdir()

    submission_root = _create_sample_submission(tmp_path)
    zip_path = submissions_dir / "project_zip.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for path in submission_root.rglob("*"):
            archive.write(path, path.relative_to(submission_root))

    config = Config(
        base_dir=base_dir,
        data_dir=Path("data"),
        reports_dir=Path("reports"),
        models_dir=Path("models"),
        intermediate_dir=Path("intermediate"),
        similarity_corpus_dir=Path("data") / "similarity_corpus",
    )

    first = run_pipeline(config=config, submission_name="project_zip")
    assert first["submissions"]
    second = run_pipeline(config=config, submission_name="project_zip")
    third = run_pipeline(config=config, submission_name="project_zip", skip_cache=True)

    second_timings = second["submissions"][0]["timings"]
    assert second_timings["video"]["cached"] is True
    assert second_timings["text"]["cached"] is True
    assert second_timings["code"]["cached"] is True

    third_timings = third["submissions"][0]["timings"]
    assert third_timings["video"]["cached"] is False
    assert third_timings["video"]["cache_skipped"] is True
    assert third_timings["text"]["cached"] is False
    assert third_timings["text"]["cache_skipped"] is True