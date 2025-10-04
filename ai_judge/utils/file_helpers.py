from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_directory(path: Path) -> Path:
    """Create the directory if missing and return the Path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_text(path: Path, default: str = "") -> str:
    """Read UTF-8 text from a file, returning a default value if it does not exist."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return default


def write_json(path: Path, payload: Any) -> None:
    """Write a JSON file with pretty formatting, ensuring the parent directory exists."""
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
