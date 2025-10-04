from __future__ import annotations

import logging
import os
from pathlib import Path
import argparse
import shutil
import zipfile
from time import perf_counter
from typing import Any, Dict, Sequence, Tuple

from .config import Config
from .modules.video_analyzer import VideoAnalyzer, VideoAnalysisResult
from .modules.text_analyzer import TextAnalyzer, TextAnalysisResult
from .modules.code_analyzer import CodeAnalyzer, CodeAnalysisResult
from .scoring.scorer import Scorer
from .scoring.criteria import JudgingCriteria
from .scoring.reporter import ReportGenerator
from .utils.cache import AnalysisCache
from .utils.fingerprint import directory_fingerprint
from .utils.file_helpers import ensure_directory
from .utils.torch_helpers import resolve_device_spec


LOGGER = logging.getLogger(__name__)
MAX_PIPELINE_SECONDS = 300

def _resolve_submission_names(
    config: Config, submission_name: str | None, submission_names: Sequence[str] | None
) -> list[str]:
    if submission_names:
        return list(submission_names)
    return [submission_name or config.default_submission_name]


def _resolve_criteria(
    config: Config, criteria: JudgingCriteria | None, criteria_path: str | Path | None
) -> JudgingCriteria:
    if criteria_path:
        return JudgingCriteria.from_json(Path(criteria_path))
    return criteria or config.load_criteria()


_ZIP_NOISE_NAMES = {"__MACOSX"}


def _prepare_submission_directory(
    config: Config, name: str, submission_path: Path
) -> Tuple[Path, Path, Path]:
    source_path = submission_path
    if submission_path.is_dir():
        normalized = _locate_submission_root(submission_path)
        return normalized, submission_path, submission_path
    if not submission_path.exists():
        zip_candidate = submission_path.parent / f"{submission_path.name}.zip"
        if zip_candidate.exists():
            source_path = zip_candidate
            submission_path = zip_candidate
    if submission_path.is_file() and submission_path.suffix.lower() == ".zip":
        extracted = _extract_submission_zip(config, name, submission_path)
        normalized = _locate_submission_root(extracted)
        return normalized, source_path, extracted
    raise FileNotFoundError(f"Submission '{name}' not found at {submission_path}.")


def _extract_submission_zip(config: Config, name: str, zip_path: Path) -> Path:
    ensure_directory(config.extracted_submissions_dir)
    extract_root = config.extracted_submissions_dir
    digest = _file_sha1(zip_path)
    destination = extract_root / f"{zip_path.stem}_{digest[:8]}"

    if not destination.exists():
        _cleanup_previous_extractions(extract_root, zip_path.stem, keep=destination)
        with zipfile.ZipFile(zip_path, "r") as archive:
            ensure_directory(destination)
            archive.extractall(destination)
    return destination


def _cleanup_previous_extractions(root: Path, stem: str, keep: Path) -> None:
    for candidate in root.glob(f"{stem}_*"):
        if candidate == keep:
            continue
        if candidate.is_dir():
            shutil.rmtree(candidate, ignore_errors=True)


def _file_sha1(path: Path, chunk_size: int = 65536) -> str:
    import hashlib

    digest = hashlib.sha1()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _friendly_path(path: Path | str, base: Path | None = None) -> str:
    try:
        resolved = Path(path).resolve(strict=False)
    except OSError:
        resolved = Path(path)
    if base is not None:
        try:
            base_resolved = Path(base).resolve(strict=False)
            return str(resolved.relative_to(base_resolved))
        except (OSError, ValueError):
            pass
    return str(resolved)


def _locate_submission_root(root: Path) -> Path:
    current = root
    visited: set[Path] = set()
    while True:
        if _has_submission_markers(current):
            break
        try:
            entries = [entry for entry in current.iterdir() if not _is_noise_entry(entry)]
        except (OSError, PermissionError):
            break

        files = [entry for entry in entries if entry.is_file()]
        directories = [entry for entry in entries if entry.is_dir()]

        if files:
            break
        if len(directories) != 1:
            break

        next_dir = directories[0]
        if next_dir in visited:
            break
        visited.add(next_dir)
        current = next_dir

    return current


def _is_noise_entry(entry: Path) -> bool:
    name = entry.name
    if name in _ZIP_NOISE_NAMES:
        return True
    if name.startswith("._"):
        return True
    return False


def _has_submission_markers(directory: Path) -> bool:
    marker_dirs = {"code", "src", "app", "project", "backend", "service"}
    for marker in marker_dirs:
        if (directory / marker).exists():
            return True

    for filename in ("description.txt", "DESCRIPTION.txt", "README.md", "README.MD", "readme.md"):
        if (directory / filename).is_file():
            return True

    try:
        for child in directory.iterdir():
            if child.is_file() and child.suffix == ".py":
                return True
    except (OSError, PermissionError):
        return False

    return False


def run_pipeline(
    config: Config | None = None,
    submission_name: str | None = None,
    submission_names: Sequence[str] | None = None,
    criteria: JudgingCriteria | None = None,
    criteria_path: str | Path | None = None,
) -> Dict[str, Any]:
    """Execute the judging pipeline for one or multiple submissions."""

    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    config = config or Config()
    reporter = ReportGenerator(config.reports_dir)
    try:
        base_root = Path(config.base_dir).resolve(strict=False)
    except OSError:
        base_root = Path(config.base_dir)
    device_spec = resolve_device_spec(config.device_preference)
    if device_spec.is_gpu:
        LOGGER.info(
            "Transformer workloads targeting %s (pipeline device %s)",
            device_spec.kind,
            device_spec.pipeline_device,
        )
    else:
        LOGGER.info("Transformer workloads using CPU execution.")
    names = _resolve_submission_names(config, submission_name, submission_names)
    judging_criteria = _resolve_criteria(config, criteria, criteria_path)

    video_analyzer = VideoAnalyzer(
        transcription_model=config.video_transcription_model,
        sentiment_model=config.video_sentiment_model,
        device_spec=device_spec,
    )
    text_analyzer = TextAnalyzer(
        similarity_corpus_dir=config.similarity_corpus_dir,
        embedding_model=config.text_embedding_model,
        top_k=config.text_similarity_top_k,
        ai_detector_model=config.text_ai_detector_model,
        device_spec=device_spec,
        ai_detector_context_length=config.text_ai_detector_context_length,
        gemini_api_key=config.gemini_api_key,
        gemini_model=config.gemini_model,
    )
    code_analyzer = CodeAnalyzer(
        gemini_api_key=config.gemini_api_key,
        gemini_model=config.gemini_model,
    )
    scorer = Scorer(judging_criteria)

    results: list[Dict[str, Any]] = []
    pipeline_start = perf_counter()
    leaderboard_duration = 0.0

    for name in names:
        submission_path = config.submission_dir(name)
        submission_dir, submission_source, extracted_root = _prepare_submission_directory(
            config, name, submission_path
        )
        stage_timings: Dict[str, Dict[str, Any]] = {}

        def _time_stage(stage_name: str, func):
            start = perf_counter()
            value = func()
            duration = perf_counter() - start
            stage_timings[stage_name] = {
                "seconds": round(duration, 4),
            }
            LOGGER.info("Stage '%s' for %s executed in %.3fs", stage_name, name, duration)
            return value

        video_result = _time_stage(
            "video",
            lambda: video_analyzer.analyze(submission_dir),
        )
        text_result = _time_stage(
            "text",
            lambda: text_analyzer.analyze(submission_dir, video_result.transcript),
        )
        code_result = _time_stage(
            "code",
            lambda: code_analyzer.analyze(submission_dir),
        )

        score = _time_stage(
            "scoring",
            lambda: scorer.score(video_result, text_result, code_result),
        )

        payload: Dict[str, Any] = {
            "submission": name,
            "submission_dir": str(submission_dir),
            "submission_dir_display": _friendly_path(submission_dir, base_root),
            "submission_source": str(submission_source),
            "submission_source_display": _friendly_path(submission_source, base_root),
            "extracted_root": str(extracted_root),
            "extracted_root_display": _friendly_path(extracted_root, base_root),
            "normalized_from_extracted": str(submission_dir) != str(extracted_root),
            "video_analysis": video_result.to_dict(),
            "text_analysis": text_result.to_dict(),
            "code_analysis": code_result.to_dict(),
            "score": score.as_dict(),
        }

        report_path = _time_stage(
            "report_generation",
            lambda: reporter.generate_submission_report(name, payload),
        )
        payload["report_path"] = str(report_path)
        payload["timings"] = stage_timings
        results.append(payload)

    leaderboard_start = perf_counter()
    leaderboard_path = reporter.generate_leaderboard(results)
    leaderboard_duration = perf_counter() - leaderboard_start
    LOGGER.info("Generated leaderboard in %.3fs", leaderboard_duration)

    pipeline_duration = perf_counter() - pipeline_start
    LOGGER.info("Pipeline completed in %.3fs", pipeline_duration)
    if pipeline_duration > MAX_PIPELINE_SECONDS:
        raise RuntimeError(
            f"Pipeline exceeded {MAX_PIPELINE_SECONDS} seconds (took {pipeline_duration:.3f}s)."
        )

    return {
        "criteria": judging_criteria.as_dict(),
        "submissions": results,
        "leaderboard_path": str(leaderboard_path),
        "run_metrics": {
            "total_runtime_seconds": round(pipeline_duration, 3),
            "leaderboard_seconds": round(leaderboard_duration, 3),
            "submission_timings": {
                entry["submission"]: entry.get("timings", {}) for entry in results
            },
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AI Hackathon judging pipeline.")
    parser.add_argument(
        "--submission",
        dest="submission",
        help="Name of a single submission (folder or .zip in data/submissions) to evaluate.",
    )
    parser.add_argument(
        "--submissions",
        nargs="+",
        dest="submissions",
        help="One or more submission names to evaluate in a single run.",
    )
    parser.add_argument(
        "--criteria",
        dest="criteria_path",
        help="Path to a custom judging criteria JSON file.",
    )
    parser.add_argument(
        "--base-dir",
        dest="base_dir",
        help="Override the project base directory (defaults to current working directory).",
    )
    parser.add_argument(
        "--device",
        dest="device",
        help="Preferred compute device (auto, cpu, cuda, cuda:<index>, mps) for local models.",
    )
    parser.add_argument(
        "--ai-detector-context",
        dest="ai_detector_context",
        type=int,
        help="Maximum characters to feed into the AI-detection pipeline.",
    )
    parser.add_argument(
        "--gemini-api-key",
        dest="gemini_api_key",
        help="Google Gemini Pro API key for AI-powered summaries (highest priority).",
    )
    parser.add_argument(
        "--gemini-model",
        dest="gemini_model",
        default="models/gemini-2.0-flash-lite",
        help="Gemini model to use (default: models/gemini-2.0-flash-lite for best free tier compatibility). Use check_gemini_models.py to see all available models.",
    )
    return parser.parse_args()


def _build_config(args: argparse.Namespace) -> Config:
    base_dir = Path(args.base_dir).resolve() if args.base_dir else Path.cwd()
    config_kwargs: Dict[str, Any] = {"base_dir": base_dir}
    if getattr(args, "device", None):
        config_kwargs["device_preference"] = args.device
    if getattr(args, "ai_detector_context", None):
        config_kwargs["text_ai_detector_context_length"] = max(512, int(args.ai_detector_context))
    
    # Gemini API key: prioritize CLI arg, then env var
    gemini_api_key = getattr(args, "gemini_api_key", None) or os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        config_kwargs["gemini_api_key"] = gemini_api_key
    
    if getattr(args, "gemini_model", None):
        config_kwargs["gemini_model"] = args.gemini_model
    return Config(**config_kwargs)


def main() -> None:
    args = _parse_args()
    config = _build_config(args)
    criteria_path = Path(args.criteria_path).resolve() if args.criteria_path else None
    run_pipeline(
        config=config,
        submission_name=args.submission,
        submission_names=args.submissions,
        criteria_path=criteria_path,
    )


if __name__ == "__main__":
    main()
