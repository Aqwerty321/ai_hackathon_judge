from __future__ import annotations

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

    video_analyzer = VideoAnalyzer()
    text_analyzer = TextAnalyzer(config.similarity_corpus_dir)
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
            "video_analysis": video_result.__dict__,
            "text_analysis": text_result.__dict__,
            "code_analysis": code_result.__dict__,
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
