from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Sequence

from .config import Config
from .modules.video_analyzer import VideoAnalyzer
from .modules.text_analyzer import TextAnalyzer
from .modules.code_analyzer import CodeAnalyzer
from .scoring.scorer import Scorer
from .scoring.criteria import JudgingCriteria
from .scoring.reporter import ReportGenerator

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

    results: list[Dict[str, Any]] = []

    for name in names:
        submission_dir = config.submission_dir(name)

        video_result = video_analyzer.analyze(submission_dir)
        text_result = text_analyzer.analyze(submission_dir)
        code_result = code_analyzer.analyze(submission_dir)

        score = scorer.score(video_result, text_result, code_result)

        payload: Dict[str, Any] = {
            "submission": name,
            "submission_dir": str(submission_dir),
            "video_analysis": asdict(video_result),
            "text_analysis": asdict(text_result),
            "code_analysis": asdict(code_result),
            "score": score.as_dict(),
        }

        report_path = reporter.generate_submission_report(name, payload)
        payload["report_path"] = str(report_path)
        results.append(payload)

    leaderboard_path = reporter.generate_leaderboard(results)

    return {
        "criteria": judging_criteria.as_dict(),
        "submissions": results,
        "leaderboard_path": str(leaderboard_path),
    }


if __name__ == "__main__":
    run_pipeline()
