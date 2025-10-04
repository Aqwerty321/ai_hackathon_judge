from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from ..modules.code_analyzer import CodeAnalysisResult
from ..modules.text_analyzer import TextAnalysisResult
from ..modules.video_analyzer import VideoAnalysisResult
from .criteria import Criterion, JudgingCriteria


@dataclass(frozen=True)
class ScoreBreakdown:
    """Normalized scores produced by the judging pipeline."""

    criteria: tuple["CriterionScore", ...]
    total: float

    def criteria_by_key(self) -> Dict[str, "CriterionScore"]:
        return {item.key: item for item in self.criteria}

    def as_dict(self) -> Dict[str, Any]:
        return {
            "total": round(self.total, 3),
            "criteria": {
                item.key: {
                    "label": item.label,
                    "weight": item.weight,
                    "normalized_weight": item.normalized_weight,
                    "raw_value": item.raw_value,
                    "normalized_value": item.normalized_value,
                    "weighted_score": item.weighted_score,
                    "description": item.description,
                }
                for item in self.criteria
            },
        }


@dataclass(frozen=True)
class CriterionScore:
    """Detailed scoring information for a single criterion."""

    key: str
    label: str
    raw_value: float
    normalized_value: float
    weight: float
    normalized_weight: float
    weighted_score: float
    description: str


class Scorer:
    """Combines modality-specific scores into a final weighted result."""

    def __init__(self, criteria: JudgingCriteria | None = None) -> None:
        self.criteria = criteria or JudgingCriteria.default()

    def score(
        self,
        video: VideoAnalysisResult,
        text: TextAnalysisResult,
        code: CodeAnalysisResult,
        extra_metrics: Mapping[str, Any] | None = None,
    ) -> ScoreBreakdown:
        context: Dict[str, Any] = {
            "video": video,
            "text": text,
            "code": code,
        }
        if extra_metrics:
            context.update(extra_metrics)

        normalized_weights = self.criteria.normalized_weights()
        criterion_scores: list[CriterionScore] = []
        total_score = 0.0

        for idx, criterion in enumerate(self.criteria.criteria):
            raw_value = self._resolve_metric(criterion, context)
            normalized_value = criterion.clamp(float(raw_value))
            normalized_weight = normalized_weights[idx]
            weighted_score = normalized_value * normalized_weight
            total_score += weighted_score
            criterion_scores.append(
                CriterionScore(
                    key=criterion.key,
                    label=criterion.label,
                    raw_value=round(float(raw_value), 3),
                    normalized_value=round(normalized_value, 3),
                    weight=round(criterion.weight, 3),
                    normalized_weight=round(normalized_weight, 3),
                    weighted_score=round(weighted_score, 3),
                    description=criterion.description,
                )
            )

        return ScoreBreakdown(criteria=tuple(criterion_scores), total=round(total_score, 3))

    def _resolve_metric(self, criterion: Criterion, context: Mapping[str, Any]) -> float:
        parts = criterion.source.split(".")
        if not parts:
            raise ValueError(f"Invalid metric source for criterion '{criterion.key}'.")

        if parts[0] not in context:
            raise KeyError(f"Unknown metric root '{parts[0]}' for criterion '{criterion.key}'.")

        value: Any = context[parts[0]]
        for part in parts[1:]:
            if isinstance(value, Mapping):
                value = value.get(part)
            else:
                value = getattr(value, part)
            if value is None:
                raise ValueError(
                    f"Metric path '{criterion.source}' for criterion '{criterion.key}' resolved to None."
                )

        if isinstance(value, (int, float)):
            return float(value)

        raise TypeError(
            f"Metric path '{criterion.source}' for criterion '{criterion.key}' must resolve to a numeric value, got {type(value)!r}."
        )
