from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


@dataclass(slots=True, frozen=True)
class Criterion:
    """Single judging criterion sourced from a metric."""

    key: str
    label: str
    weight: float
    source: str
    description: str = ""
    min_value: float = 0.0
    max_value: float = 1.0

    def clamp(self, raw_value: float) -> float:
        if self.max_value <= self.min_value:
            return raw_value
        span = self.max_value - self.min_value
        normalized = (raw_value - self.min_value) / span
        return max(0.0, min(1.0, normalized))


@dataclass(slots=True, frozen=True)
class JudgingCriteria:
    """Collection of criteria used for weighted scoring."""

    criteria: tuple[Criterion, ...]

    @property
    def total_weight(self) -> float:
        return sum(item.weight for item in self.criteria)

    def normalized_weights(self) -> tuple[float, ...]:
        total = self.total_weight
        if total <= 0:
            raise ValueError("Criteria weights must sum to a positive value.")
        return tuple(item.weight / total for item in self.criteria)

    def as_dict(self) -> dict[str, Mapping[str, float | str]]:
        return {
            item.key: {
                "label": item.label,
                "weight": item.weight,
                "source": item.source,
                "description": item.description,
                "min_value": item.min_value,
                "max_value": item.max_value,
            }
            for item in self.criteria
        }

    @classmethod
    def from_sequence(cls, items: Iterable[Mapping[str, object]]) -> "JudgingCriteria":
        criteria = []
        for entry in items:
            criteria.append(
                Criterion(
                    key=str(entry["key"]),
                    label=str(entry.get("label", entry["key"])),
                    weight=float(entry.get("weight", 0.0)),
                    source=str(entry["source"]),
                    description=str(entry.get("description", "")),
                    min_value=float(entry.get("min_value", 0.0)),
                    max_value=float(entry.get("max_value", 1.0)),
                )
            )
        return cls(tuple(criteria))

    @classmethod
    def from_json(cls, path: Path) -> "JudgingCriteria":
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data["criteria"] if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise ValueError("Criteria JSON must define a list of criteria.")
        return cls.from_sequence(items)

    @classmethod
    def default(cls) -> "JudgingCriteria":
        return cls.from_sequence(
            [
                {
                    "key": "originality",
                    "label": "Originality",
                    "weight": 0.30,
                    "source": "text.originality_score",
                    "description": "Measured from lexical uniqueness in the project description.",
                },
                {
                    "key": "technical_feasibility",
                    "label": "Technical Feasibility",
                    "weight": 0.25,
                    "source": "text.feasibility_score",
                    "description": "Log-scaled feasibility estimate derived from description word count.",
                },
                {
                    "key": "presentation_quality",
                    "label": "Presentation Quality",
                    "weight": 0.20,
                    "source": "video.clarity_score",
                    "description": "Clarity heuristics computed from the presentation transcript.",
                },
                {
                    "key": "code_quality",
                    "label": "Code Quality & Correctness",
                    "weight": 0.25,
                    "source": "code.quality_index",
                    "description": "Average of readability, documentation, and coverage heuristics.",
                },
            ]
        )
