from pathlib import Path

import pandas as pd

from ai_judge.scoring.reporter import ReportGenerator


def _sample_payload(tmp_path: Path) -> dict:
    return {
        "submission": "alpha",
        "submission_dir": str(tmp_path / "submissions" / "alpha"),
        "score": {
            "total": 0.876,
            "criteria": {
                "presentation": {
                    "label": "Presentation",
                    "normalized_weight": 0.5,
                    "raw_value": 0.9,
                    "normalized_value": 0.9,
                    "weighted_score": 0.45,
                    "description": "Clarity of the pitch",
                },
                "impact": {
                    "label": "Impact",
                    "normalized_weight": 0.5,
                    "raw_value": 0.85,
                    "normalized_value": 0.85,
                    "weighted_score": 0.425,
                    "description": "Expected market impact",
                },
            },
        },
        "video_analysis": {
            "transcript": "We built an AI assistant that streamlines business workflows and improves productivity dramatically.",
            "clarity_score": 0.82,
            "estimated_duration_seconds": 95.0,
            "sentiment_label": "positive",
            "sentiment_score": 0.91,
            "transcription_source": "submission_transcript",
        },
        "text_analysis": {
            "originality_score": 0.77,
            "feasibility_score": 0.66,
            "summary": "AI assistant automating repetitive business operations for SMEs.",
            "similarity_matches": [
                {
                    "source": "automation_whitepaper",
                    "score": 0.41,
                    "snippet": "Workflow automation for small teams",
                }
            ],
            "suspect_claims": [
                {
                    "statement": "Cuts operational costs by 80% in one month",
                    "reason": "Large impact claim",
                    "llm_verdict": "needs_verification",
                    "llm_rationale": "Requires empirical backing",
                }
            ],
            "ai_generated_likelihood": 0.18,
        },
        "code_analysis": {
            "readability_score": 0.71,
            "documentation_score": 0.64,
            "test_coverage_score_estimate": 0.5,
            "details": {
                "lint": {
                    "status": "ok",
                    "messages": [
                        {
                            "symbol": "unused-import",
                            "path": "app.py",
                            "line": 4,
                            "message": "Unused import 'os'",
                        }
                    ],
                },
                "complexity": {
                    "status": "ok",
                    "average_complexity": 3.2,
                    "normalized_score": 0.644,
                    "files": [
                        {
                            "path": "app.py",
                            "max_complexity": 4.5,
                            "average_complexity": 3.2,
                        }
                    ],
                },
                "documentation": {
                    "status": "ok",
                    "objects": 6,
                    "docstrings": 4,
                    "ratio": 0.667,
                    "errors": [],
                },
                "pytest": {
                    "status": "passed",
                    "returncode": 0,
                    "output": "1 passed in 0.03s",
                },
            },
        },
    }


def test_generate_submission_report_creates_rich_html(tmp_path: Path) -> None:
    payload = _sample_payload(tmp_path)
    reporter = ReportGenerator(tmp_path)

    report_path = reporter.generate_submission_report("alpha", payload)

    html = Path(report_path).read_text(encoding="utf-8")
    assert report_path.suffix == ".html"
    assert "AI Hackathon Report: alpha" in html
    assert "Clarity" in html
    assert "Similarity matches" in html
    assert "Unused import 'os'" in html
    assert "Pytest output" in html


def test_generate_leaderboard_aggregates_dataframe(tmp_path: Path) -> None:
    reporter = ReportGenerator(tmp_path)

    submissions = [
        _sample_payload(tmp_path),
        {
            **_sample_payload(tmp_path),
            "submission": "beta",
            "score": {
                "total": 0.654,
                "criteria": {},
            },
            "video_analysis": {
                "clarity_score": 0.6,
                "sentiment_score": 0.2,
            },
            "text_analysis": {
                "originality_score": 0.4,
                "feasibility_score": 0.5,
            },
            "code_analysis": {
                "readability_score": 0.3,
                "documentation_score": 0.2,
                "test_coverage_score_estimate": 0.1,
            },
        },
    ]

    leaderboard_path = reporter.generate_leaderboard(submissions)

    df = pd.read_csv(leaderboard_path)
    assert list(df.columns) == [
        "rank",
        "submission",
        "total_score",
        "video_clarity",
        "video_sentiment",
        "text_originality",
        "text_feasibility",
        "code_readability",
        "code_documentation",
        "code_test_estimate",
    ]
    assert df.iloc[0]["submission"] == "alpha"
    assert df.iloc[0]["rank"] == 1
    assert df.iloc[1]["rank"] == 2