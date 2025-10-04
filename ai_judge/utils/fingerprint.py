from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

IGNORED_DIRECTORIES = {"__pycache__"}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp"}


def directory_fingerprint(root: Path, include_suffixes: Iterable[str] | None = None) -> str:
    """Compute a deterministic fingerprint for files under ``root``."""
    include = set(include_suffixes or [])
    digest = hashlib.sha1()

    for path in sorted(root.rglob("*")):
        if path.is_dir():
            if path.name in IGNORED_DIRECTORIES:
                continue
            continue
        if include and path.suffix not in include:
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(str(stat.st_mtime_ns).encode("utf-8"))
        digest.update(str(stat.st_size).encode("utf-8"))

    return digest.hexdigest()
