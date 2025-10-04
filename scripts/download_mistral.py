"""Utility script to fetch the Mistral-7B-Instruct Q4_K_M GGUF model.

Usage:
    python scripts/download_mistral.py

Requires:
    pip install huggingface_hub

The script saves the model file under models/mistral-7b-instruct.Q4_K_M.gguf by
streaming it from the Hugging Face Hub. If you have not agreed to the model
license, visit https://huggingface.co/TheBloke/Mistral-7B-Instruct-GGUF first
and click the "Access repository" button.
"""

from __future__ import annotations

import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

MODEL_REPO = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
MODEL_FILENAME = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"


def main() -> None:
    target_dir = Path("models")
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {MODEL_FILENAME} from {MODEL_REPO}...")
    local_path = hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILENAME)

    destination = target_dir / MODEL_FILENAME
    if Path(local_path) == destination:
        print(f"Model already present at {destination}")
        return

    print(f"Copying to {destination}")
    destination.write_bytes(Path(local_path).read_bytes())
    print("Download complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - convenience script
        print(f"Failed to download model: {exc}", file=sys.stderr)
        raise
