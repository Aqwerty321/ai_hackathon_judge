from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import pandas as pd
from jinja2 import Environment, PackageLoader, select_autoescape

from ..utils.file_helpers import ensure_directory

try:  # pragma: no cover - optional dependency used for visualizations
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - gracefully skip charts without matplotlib
    plt = None  # type: ignore
    matplotlib = None  # type: ignore

try:  # pragma: no cover - optional dependency for markdown rendering
    import markdown
except ImportError:  # pragma: no cover
    markdown = None  # type: ignore


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
        # Add markdown filter for rendering AI insights
        def markdown_filter(text):
            if not text:
                return ""
            if markdown is not None:
                try:
                    return markdown.markdown(
                        text,
                        extensions=['extra', 'nl2br', 'sane_lists']
                    )
                except Exception:
                    # Fallback to plain text if markdown fails
                    return text
            return text
        
        self._env.filters['markdown'] = markdown_filter

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
        gemini_insights = details.get("gemini_insights") if isinstance(details, Mapping) else None

        top_matches = list(text.get("similarity_matches") or [])[:3]
        claims = list(text.get("suspect_claims") or [])

        chart_paths = self._build_charts(submission_name, score_section, video, text, code)

        submission_dir_display = (
            payload.get("submission_dir_display")
            or payload.get("submission_dir")
            or "Unknown"
        )
        submission_source_display = (
            payload.get("submission_source_display")
            or payload.get("submission_source")
            or None
        )
        extracted_root_display = (
            payload.get("extracted_root_display")
            or payload.get("extracted_root")
            or None
        )
        normalized_from_extracted = bool(payload.get("normalized_from_extracted"))

        context = {
            "submission_name": submission_name,
            "submission_dir": submission_dir_display,
            "submission_source": submission_source_display,
            "extracted_root": extracted_root_display,
            "normalized_from_extracted": normalized_from_extracted,
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
            "gemini_insights": gemini_insights,
            "charts": chart_paths,
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

    def _chart_dir(self, submission_name: str) -> Path:
        charts_dir = self.output_dir / "charts"
        ensure_directory(charts_dir)
        submission_dir = charts_dir / submission_name
        ensure_directory(submission_dir)
        return submission_dir

    def _build_charts(
        self,
        submission_name: str,
        score_section: Mapping[str, Any],
        video: Mapping[str, Any],
        text: Mapping[str, Any],
        code: Mapping[str, Any],
    ) -> Dict[str, str]:
        if plt is None:
            return {}

        charts: Dict[str, str] = {}
        target_dir = self._chart_dir(submission_name)

        self._plot_scores(target_dir, score_section, charts)
        self._plot_video_metrics(target_dir, video, charts)
        self._plot_text_metrics(target_dir, text, charts)
        self._plot_code_metrics(target_dir, code, charts)

        return charts

    def _plot_scores(
        self,
        target_dir: Path,
        score_section: Mapping[str, Any],
        charts: Dict[str, str],
    ) -> None:
        criteria = score_section.get("criteria", {}) if isinstance(score_section, Mapping) else {}
        if not criteria:
            return
        labels = []
        weighted = []
        raw = []
        for key, entry in criteria.items():
            try:
                labels.append(str(entry.get("label") or key))
                weighted.append(float(entry.get("weighted_score", 0.0)))
                raw.append(float(entry.get("normalized_value", 0.0)))
            except (TypeError, ValueError):
                continue
        if not labels:
            return
        fig, ax = plt.subplots(figsize=(6.5, 4))
        index = range(len(labels))
        ax.bar(index, weighted, label="Weighted", color="#4CAF50", alpha=0.8)
        ax.plot(index, raw, label="Normalized", color="#2196F3", marker="o", linewidth=2)
        ax.set_xticks(list(index))
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_ylabel("Score")
        ax.set_title("Criteria Scores", pad=12)
        ax.legend()
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        output_path = target_dir / "scores.png"
        fig.savefig(output_path, dpi=150)
        plt.close(fig)
        charts["scores"] = self._relative_chart_path(output_path)

    def _plot_video_metrics(
        self,
        target_dir: Path,
        video: Mapping[str, Any],
        charts: Dict[str, str],
    ) -> None:
        if not video:
            return
        labels = ["Clarity", "Sentiment"]
        values = []
        try:
            values.append(float(video.get("clarity_score", 0.0)))
            values.append(float(video.get("sentiment_score", 0.0)))
        except (TypeError, ValueError):
            return
        fig, ax = plt.subplots(figsize=(4.5, 3.5))
        bars = ax.bar(labels, values, color=["#FF9800", "#03A9F4"])
        ax.set_ylim(0, 1)
        ax.set_title("Video Metrics", pad=12)
        ax.bar_label(bars, fmt="%.2f")
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        output_path = target_dir / "video_metrics.png"
        fig.savefig(output_path, dpi=150)
        plt.close(fig)
        charts["video_metrics"] = self._relative_chart_path(output_path)

    def _plot_text_metrics(
        self,
        target_dir: Path,
        text: Mapping[str, Any],
        charts: Dict[str, str],
    ) -> None:
        if not text:
            return
        metrics = [
            ("Originality", text.get("originality_score", 0.0)),
            ("Feasibility", text.get("feasibility_score", 0.0)),
            ("AI Likelihood", text.get("ai_generated_likelihood", 0.0)),
        ]
        labels = []
        values = []
        for label, value in metrics:
            try:
                labels.append(label)
                values.append(float(value))
            except (TypeError, ValueError):
                continue
        if not labels:
            return
        fig, ax = plt.subplots(figsize=(4.5, 3.5))
        bars = ax.bar(labels, values, color=["#8BC34A", "#673AB7", "#E91E63"])
        ax.set_ylim(0, 1)
        ax.set_title("Text Metrics", pad=12)
        ax.bar_label(bars, fmt="%.2f")
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        output_path = target_dir / "text_metrics.png"
        fig.savefig(output_path, dpi=150)
        plt.close(fig)
        charts["text_metrics"] = self._relative_chart_path(output_path)

    def _plot_code_metrics(
        self,
        target_dir: Path,
        code: Mapping[str, Any],
        charts: Dict[str, str],
    ) -> None:
        if not code:
            return
        metrics = [
            ("Readability", code.get("readability_score", 0.0)),
            ("Documentation", code.get("documentation_score", 0.0)),
            ("Tests", code.get("test_coverage_score_estimate", 0.0)),
        ]
        labels = []
        values = []
        for label, value in metrics:
            try:
                labels.append(label)
                values.append(float(value))
            except (TypeError, ValueError):
                continue
        if not labels:
            return
        fig, ax = plt.subplots(figsize=(4.5, 3.5))
        bars = ax.bar(labels, values, color=["#009688", "#FF5722", "#607D8B"])
        ax.set_ylim(0, 1)
        ax.set_title("Code Metrics", pad=12)
        ax.bar_label(bars, fmt="%.2f")
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        output_path = target_dir / "code_metrics.png"
        fig.savefig(output_path, dpi=150)
        plt.close(fig)
        charts["code_metrics"] = self._relative_chart_path(output_path)

    def _relative_chart_path(self, chart_path: Path) -> str:
        return str(chart_path.relative_to(self.output_dir))
