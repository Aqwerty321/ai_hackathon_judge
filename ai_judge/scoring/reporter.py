from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import pandas as pd
from jinja2 import Environment, PackageLoader, select_autoescape

from ..utils.file_helpers import ensure_directory


@dataclass(slots=True)
class ReportGenerator:
    """Generates submission reports and an aggregated leaderboard."""

    output_dir: Path
    _env: Environment = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._env = Environment(  # pragma: no cover - template configuration
            loader=PackageLoader("ai_judge", "templates"),
            autoescape=select_autoescape(("html", "xml")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_submission_report(self, submission_name: str, payload: Mapping[str, Any]) -> Path:
        ensure_directory(self.output_dir)
        report_path = self.output_dir / f"{submission_name}_report.html"

        score_section = payload.get("score", {})
        criteria_map: Mapping[str, Dict[str, Any]] = score_section.get("criteria", {})
        criteria = [
            {
                "key": key,
                **entry,
            }
            for key, entry in criteria_map.items()
        ]
        criteria.sort(key=lambda item: item.get("normalized_weight", 0.0), reverse=True)

        video = dict(payload.get("video_analysis", {}))
        text = dict(payload.get("text_analysis", {}))
        code = dict(payload.get("code_analysis", {}))
        details = code.get("details") or {}

        lint_section = details.get("lint") if isinstance(details, Mapping) else {}
        lint_messages = []
        if isinstance(lint_section, Mapping):
            lint_messages = list(lint_section.get("messages") or [])[:5]

        complexity_section = details.get("complexity") if isinstance(details, Mapping) else {}
        documentation_section = details.get("documentation") if isinstance(details, Mapping) else {}
        pytest_section = details.get("pytest") if isinstance(details, Mapping) else {}

        top_matches = list(text.get("similarity_matches") or [])[:3]
        claims = list(text.get("suspect_claims") or [])

        context = {
            "submission_name": submission_name,
            "submission_dir": payload.get("submission_dir", "Unknown"),
            "score_total": f"{score_section.get('total', 0):.3f}",
            "criteria": criteria,
            "video": video,
            "video_excerpt": self._excerpt(video.get("transcript", "")),
            "text": text,
            "top_matches": top_matches,
            "claims": claims,
            "code": code,
            "lint_messages": lint_messages,
            "complexity": complexity_section,
            "documentation": documentation_section,
            "pytest_details": pytest_section,
        }

        template = self._env.get_template("submission_report.html.j2")
        report_path.write_text(template.render(**context), encoding="utf-8")
        return report_path

    def generate_leaderboard(self, submissions: Sequence[Mapping[str, Any]]) -> Path:
        ensure_directory(self.output_dir)
        leaderboard_path = self.output_dir / "leaderboard.csv"

        rows: list[Dict[str, Any]] = []
        for entry in submissions:
            score = entry.get("score", {})
            video = entry.get("video_analysis", {})
            text = entry.get("text_analysis", {})
            code = entry.get("code_analysis", {})
            rows.append(
                {
                    "submission": entry.get("submission", "unknown"),
                    "total_score": score.get("total", 0.0),
                    "video_clarity": (video or {}).get("clarity_score", 0.0),
                    "video_sentiment": (video or {}).get("sentiment_score", 0.0),
                    "text_originality": (text or {}).get("originality_score", 0.0),
                    "text_feasibility": (text or {}).get("feasibility_score", 0.0),
                    "code_readability": (code or {}).get("readability_score", 0.0),
                    "code_documentation": (code or {}).get("documentation_score", 0.0),
                    "code_test_estimate": (code or {}).get("test_coverage_score_estimate", 0.0),
                }
            )

        df = pd.DataFrame(rows)
        if df.empty:
            df = pd.DataFrame(
                columns=[
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
            )
        else:
            df.sort_values("total_score", ascending=False, inplace=True)
            df.reset_index(drop=True, inplace=True)
            df.insert(0, "rank", df.index + 1)

        df.to_csv(leaderboard_path, index=False)
        return leaderboard_path

    @staticmethod
    def _excerpt(text: str, max_chars: int = 400) -> str:
        snippet = (text or "").strip()
        if not snippet:
            return "No transcript available."
        if len(snippet) <= max_chars:
            return snippet
        return snippet[: max_chars - 1].rsplit(" ", 1)[0] + "…"
