from __future__ import annotations

import json
from pathlib import Path
from typing import Any, NamedTuple, Optional


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


def read_json(path: Path) -> Optional[Any]:
    """Read JSON content from a file, returning None if it does not exist or is invalid."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


class SubmissionDescription(NamedTuple):
    text: str
    source: str


def read_submission_description(submission_dir: Path) -> SubmissionDescription:
    """Return the best available textual description for a submission.

    Preference order:
        1. description.txt / DESCRIPTION.txt
        2. description.md / DESCRIPTION.md
        3. README files (md/txt variants)

    The returned source string indicates which file supplied the content or
    'missing' if none were found.
    """

    candidates = [
        ("description.txt", "description_fallback"),
        ("DESCRIPTION.TXT", "description_fallback"),
        ("description.md", "description_fallback"),
        ("DESCRIPTION.MD", "description_fallback"),
        ("README.md", "readme_fallback"),
        ("readme.md", "readme_fallback"),
        ("README.MD", "readme_fallback"),
        ("README.txt", "readme_fallback"),
        ("readme.txt", "readme_fallback"),
    ]

    for filename, label in candidates:
        content = read_text(submission_dir / filename)
        if content.strip():
            return SubmissionDescription(content, label)

    return SubmissionDescription("", "missing")
