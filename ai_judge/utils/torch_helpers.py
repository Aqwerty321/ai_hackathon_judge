from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class DeviceSpec:
    """Represents the preferred execution device for torch/transformer workloads."""

    kind: str
    pipeline_device: Union[int, str]

    @property
    def sentence_transformer_device(self) -> str:
        if self.kind == "cuda":
            if isinstance(self.pipeline_device, int):
                return f"cuda:{self.pipeline_device}"
            if isinstance(self.pipeline_device, str) and self.pipeline_device not in {"cpu", "cuda"}:
                return self.pipeline_device
            return "cuda"
        if self.kind == "mps":
            return "mps"
        return "cpu"

    @property
    def is_gpu(self) -> bool:
        return self.kind in {"cuda", "mps"}


def _import_torch():  # pragma: no cover - optional dependency
    try:
        import torch  # type: ignore

        return torch  # type: ignore
    except Exception:  # pragma: no cover - gracefully degrade when torch missing
        return None


def resolve_device_spec(preference: str | None = "auto") -> DeviceSpec:
    """Resolve a device preference into concrete execution targets.

    Parameters
    ----------
    preference:
        User-specified preference. Supported values (case insensitive):
        "auto", "cpu", "cuda", "gpu", "cuda:<index>", "mps".

    Returns
    -------
    DeviceSpec
        Structure containing the resolved device for libraries that expect a
        string (e.g. SentenceTransformer) and the appropriate argument for
        Transformers pipelines (which typically accept either an integer index
        or a device string).
    """

    torch = _import_torch()
    pref = (preference or "auto").lower().strip()

    has_cuda = bool(torch and getattr(torch.cuda, "is_available", lambda: False)())
    cuda_count = int(torch.cuda.device_count()) if torch and has_cuda else 0
    has_mps = bool(
        torch
        and getattr(torch.backends, "mps", None) is not None
        and torch.backends.mps.is_available()
    )

    # Explicit CPU request or no torch backend available.
    if pref in {"cpu", "none"} or torch is None:
        return DeviceSpec(kind="cpu", pipeline_device="cpu")

    # Explicit CUDA device e.g. cuda:1
    if pref.startswith("cuda") or pref.startswith("gpu"):
        index = 0
        if ":" in pref:
            try:
                index = int(pref.split(":", 1)[1])
            except ValueError:
                index = 0
        if has_cuda and index < cuda_count:
            return DeviceSpec(kind="cuda", pipeline_device=index)
        # Fall back to default GPU if available
        if has_cuda:
            return DeviceSpec(kind="cuda", pipeline_device=0)
        # Requested CUDA but unavailable -> fallback to CPU
        return DeviceSpec(kind="cpu", pipeline_device="cpu")

    if pref == "mps":
        if has_mps:
            return DeviceSpec(kind="mps", pipeline_device="mps")
        return DeviceSpec(kind="cpu", pipeline_device="cpu")

    # Automatic selection
    if pref == "auto":
        if has_cuda:
            return DeviceSpec(kind="cuda", pipeline_device=0)
        if has_mps:
            return DeviceSpec(kind="mps", pipeline_device="mps")
        return DeviceSpec(kind="cpu", pipeline_device="cpu")

    # Unrecognised preference -> conservative CPU fallback
    return DeviceSpec(kind="cpu", pipeline_device="cpu")
