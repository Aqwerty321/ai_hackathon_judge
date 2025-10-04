from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Sequence

from .config import Config
from .modules.video_analyzer import VideoAnalyzer, VideoAnalysisResult
from .modules.text_analyzer import TextAnalyzer, TextAnalysisResult
from .modules.code_analyzer import CodeAnalyzer, CodeAnalysisResult
from .scoring.scorer import Scorer
from .scoring.criteria import JudgingCriteria
from .scoring.reporter import ReportGenerator
from .utils.cache import AnalysisCache
from .utils.fingerprint import directory_fingerprint


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
    names = _resolve_submission_names(config, submission_name, submission_names)
    judging_criteria = _resolve_criteria(config, criteria, criteria_path)

    video_analyzer = VideoAnalyzer(
        intermediate_dir=config.transcript_cache_dir,
        transcription_model=config.video_transcription_model,
        sentiment_model=config.video_sentiment_model,
    )
    text_analyzer = TextAnalyzer(
        similarity_corpus_dir=config.similarity_corpus_dir,
        intermediate_dir=config.text_cache_dir,
        embedding_model=config.text_embedding_model,
        top_k=config.text_similarity_top_k,
        ai_detector_model=config.text_ai_detector_model,
        llm_model_path=config.resolved_text_llm_model_path,
        llm_model_type=config.text_llm_model_type,
        llm_max_tokens=config.text_llm_max_tokens,
    )
    code_analyzer = CodeAnalyzer()
    scorer = Scorer(judging_criteria)
    cache = AnalysisCache(config.analysis_cache_dir)

    results: list[Dict[str, Any]] = []
    pipeline_start = perf_counter()
    leaderboard_duration = 0.0

    for name in names:
        submission_dir = config.submission_dir(name)
        fingerprint = directory_fingerprint(submission_dir)
        stage_timings: Dict[str, Dict[str, Any]] = {}

        def _run_stage(
            stage_name: str,
            compute,
            serializer,
            loader,
        ):
            cached_payload = cache.load(name, stage_name, fingerprint)
            if cached_payload is not None:
                start_cached = perf_counter()
                result = loader(cached_payload)
                cached_duration = perf_counter() - start_cached
                stage_timings[stage_name] = {
                    "seconds": round(cached_duration, 4),
                    "cached": True,
                }
                LOGGER.info("Stage '%s' for %s served from cache in %.3fs", stage_name, name, cached_duration)
                return result

            start = perf_counter()
            result = compute()
            duration = perf_counter() - start
            cache.store(name, stage_name, fingerprint, serializer(result))
            stage_timings[stage_name] = {
                "seconds": round(duration, 4),
                "cached": False,
            }
            LOGGER.info("Stage '%s' for %s executed in %.3fs", stage_name, name, duration)
            return result

        def _time_stage(stage_name: str, func):
            start = perf_counter()
            value = func()
            duration = perf_counter() - start
            stage_timings[stage_name] = {
                "seconds": round(duration, 4),
                "cached": False,
            }
            LOGGER.info("Stage '%s' for %s executed in %.3fs", stage_name, name, duration)
            return value

        video_result = _run_stage(
            "video",
            lambda: video_analyzer.analyze(submission_dir),
            lambda res: res.to_dict(),
            lambda data: VideoAnalysisResult.from_dict(data),
        )
        text_result = _run_stage(
            "text",
            lambda: text_analyzer.analyze(submission_dir),
            lambda res: res.to_dict(),
            lambda data: TextAnalysisResult.from_dict(data),
        )
        code_result = _run_stage(
            "code",
            lambda: code_analyzer.analyze(submission_dir),
            lambda res: res.to_dict(),
            lambda data: CodeAnalysisResult.from_dict(data),
        )

        score = _time_stage(
            "scoring",
            lambda: scorer.score(video_result, text_result, code_result),
        )

        payload: Dict[str, Any] = {
            "submission": name,
            "submission_dir": str(submission_dir),
            "fingerprint": fingerprint,
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


if __name__ == "__main__":
    run_pipeline()
