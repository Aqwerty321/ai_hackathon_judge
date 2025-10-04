from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from ..utils.file_helpers import ensure_directory


@dataclass(slots=True)
class ReportGenerator:
    """Generates submission reports and an aggregated leaderboard."""

    output_dir: Path

    def generate_submission_report(self, submission_name: str, payload: Mapping[str, Any]) -> Path:
        ensure_directory(self.output_dir)
        report_path = self.output_dir / f"{submission_name}_report.txt"

        score_section = payload.get("score", {})
        criteria = score_section.get("criteria", {})

        lines = [f"AI Hackathon Report: {submission_name}", "=" * 60, ""]
        lines.append("Submission directory: " + str(payload.get("submission_dir", "Unknown")))
        lines.append("Total score: " + f"{score_section.get('total', 0):.3f}")
        lines.append("")
        lines.append("Criteria Breakdown:")

        for key, entry in criteria.items():
            label = entry.get("label", key)
            weight_pct = entry.get("normalized_weight", 0) * 100
            lines.append(
                f"- {label} [{weight_pct:.1f}% weight]\n"
                f"  Raw: {entry.get('raw_value', 0):.3f}, Normalized: {entry.get('normalized_value', 0):.3f}, "
                f"Weighted contribution: {entry.get('weighted_score', 0):.3f}"
            )
            description = entry.get("description")
            if description:
                lines.append(f"  Notes: {description}")

        lines.append("")
        lines.append("Analysis Highlights:")
        lines.append("  Video: " + str(payload.get("video_analysis")))
        lines.append("  Text: " + str(payload.get("text_analysis")))
        lines.append("  Code: " + str(payload.get("code_analysis")))

        report_path.write_text("\n".join(lines), encoding="utf-8")
        return report_path

    def generate_leaderboard(self, submissions: Sequence[Mapping[str, Any]]) -> Path:
        ensure_directory(self.output_dir)
        leaderboard_path = self.output_dir / "leaderboard.csv"

        sorted_entries = sorted(
            submissions,
            key=lambda item: item.get("score", {}).get("total", 0.0),
            reverse=True,
        )

        header = ["rank", "submission", "total_score"]
        lines = [",".join(header)]
        for idx, entry in enumerate(sorted_entries, start=1):
            submission = entry.get("submission", f"submission_{idx}")
            total_score = entry.get("score", {}).get("total", 0.0)
            lines.append(f"{idx},{submission},{total_score:.3f}")

        leaderboard_path.write_text("\n".join(lines), encoding="utf-8")
        return leaderboard_path
