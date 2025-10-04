from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from .file_helpers import ensure_directory, read_json, write_json


class AnalysisCache:
    """Lightweight JSON cache for analyzer outputs keyed by submission fingerprint."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = ensure_directory(base_dir)

    def _stage_path(self, submission: str, stage: str) -> Path:
        return self.base_dir / submission / f"{stage}.json"

    def load(self, submission: str, stage: str, fingerprint: str) -> Any | None:
        """Return cached payload for the given submission/stage if fingerprint matches."""
        data = read_json(self._stage_path(submission, stage))
        if not isinstance(data, Mapping):
            return None
        if data.get("fingerprint") != fingerprint:
            return None
        return data.get("payload")

    def store(self, submission: str, stage: str, fingerprint: str, payload: Any) -> None:
        """Persist payload for a submission/stage combination."""
        if is_dataclass(payload):
            payload = asdict(payload)
        write_json(
            self._stage_path(submission, stage),
            {
                "fingerprint": fingerprint,
                "payload": payload,
            },
        )
