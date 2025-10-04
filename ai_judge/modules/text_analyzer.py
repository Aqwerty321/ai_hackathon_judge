from __future__ import annotations

import math
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

from ..utils.file_helpers import ensure_directory, read_text

try:  # pragma: no cover - optional heavy dependencies
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError:  # pragma: no cover - optional heavy dependencies
    SentenceTransformer = None  # type: ignore

try:  # pragma: no cover - optional heavy dependencies
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover - optional heavy dependencies
    np = None  # type: ignore

try:  # pragma: no cover - optional heavy dependencies
    from transformers import pipeline  # type: ignore
except ImportError:  # pragma: no cover - optional heavy dependencies
    pipeline = None  # type: ignore


@dataclass(frozen=True)
class SimilarityMatch:
    """Top-k similarity result from the reference corpus."""

    source: str
    score: float
    snippet: str


@dataclass(frozen=True)
class ClaimFlag:
    """Represents a potentially exaggerated or unverifiable claim."""

    statement: str
    reason: str


@dataclass(frozen=True)
class TextAnalysisResult:
    """Results of analyzing the written project description."""

    originality_score: float
    feasibility_score: float
    summary: str
    similarity_matches: Tuple[SimilarityMatch, ...]
    suspect_claims: Tuple[ClaimFlag, ...]
    ai_generated_likelihood: float


class TextAnalyzer:
    """Hybrid text analyzer blending heuristics with optional ML models."""

    def __init__(
        self,
        similarity_corpus_dir: Path | None = None,
        intermediate_dir: Path | None = None,
        embedding_model: str | None = None,
        top_k: int = 5,
        ai_detector_model: str | None = None,
    ) -> None:
        self.similarity_corpus_dir = Path(similarity_corpus_dir) if similarity_corpus_dir else None
        self._cache_dir = Path(intermediate_dir) if intermediate_dir else None
        if self._cache_dir:
            ensure_directory(self._cache_dir)
        self._embedding_model_name = embedding_model
        self._ai_detector_model = ai_detector_model
        self._top_k = top_k

        self._embedder = None
        self._ai_detector = None
        self._corpus_cache: list[tuple[str, str]] | None = None

    def analyze(self, submission_dir: Path) -> TextAnalysisResult:
        description = read_text(submission_dir / "description.txt")
        word_count = len(description.split())
        matches = self._compute_similarity(description)
        originality = self._estimate_originality(description, matches)
        feasibility = self._estimate_feasibility(word_count)
        summary = self._summarize(description)
        claims = self._flag_claims(description)
        ai_likelihood = self._estimate_ai_generated(description)

        return TextAnalysisResult(
            originality_score=originality,
            feasibility_score=feasibility,
            summary=summary,
            similarity_matches=tuple(matches),
            suspect_claims=tuple(claims),
            ai_generated_likelihood=round(ai_likelihood, 3),
        )

    # ------------------------------------------------------------------
    # Core heuristics
    def _estimate_originality(
        self, description: str, matches: Iterable[SimilarityMatch] | None = None
    ) -> float:
        if not description.strip():
            return 0.0
        tokens = description.split()
        unique_tokens = len({token.lower() for token in tokens})
        lexical_uniqueness = unique_tokens / len(tokens) if tokens else 0.0
        similarity_penalty = 0.0
        if matches:
            similarity_penalty = max(match.score for match in matches) * 0.4
        score = max(0.0, lexical_uniqueness - similarity_penalty)
        return round(min(1.0, score), 3)

    def _estimate_feasibility(self, word_count: int) -> float:
        if word_count == 0:
            return 0.0
        return round(min(1.0, math.log(word_count + 1, 10)), 3)

    def _summarize(self, description: str, max_words: int = 40) -> str:
        if not description.strip():
            return "No project description provided."
        tokens = description.split()
        if len(tokens) <= max_words:
            return description.strip()
        return " ".join(tokens[:max_words]) + "..."

    # ------------------------------------------------------------------
    # Similarity detection
    def _load_corpus(self) -> list[tuple[str, str]]:
        if self._corpus_cache is not None:
            return self._corpus_cache
        corpus: list[tuple[str, str]] = []
        if self.similarity_corpus_dir and self.similarity_corpus_dir.exists():
            for path in self.similarity_corpus_dir.rglob("*.txt"):
                text = read_text(path)
                if text.strip():
                    corpus.append((path.stem, text))
        self._corpus_cache = corpus
        return corpus

    def _compute_similarity(self, description: str) -> list[SimilarityMatch]:
        description = description.strip()
        if not description:
            return []
        corpus = self._load_corpus()
        if not corpus:
            return []

        if SentenceTransformer and self._embedding_model_name:
            return self._embedding_similarity(description, corpus)

        return self._lexical_similarity(description, corpus)

    def _embedding_similarity(
        self, description: str, corpus: Iterable[tuple[str, str]]
    ) -> list[SimilarityMatch]:  # pragma: no cover - depends on optional libs
        try:
            if self._embedder is None:
                self._embedder = SentenceTransformer(self._embedding_model_name)
            query_vec = self._embedder.encode(description, normalize_embeddings=True)
            matches: list[SimilarityMatch] = []
            for key, text in corpus:
                corpus_vec = self._embedder.encode(text, normalize_embeddings=True)
                if np is not None:
                    score = float(np.clip(np.dot(query_vec, corpus_vec), -1.0, 1.0))
                else:
                    score = float(sum(a * b for a, b in zip(query_vec, corpus_vec)))
                snippet = self._snippet(text)
                matches.append(SimilarityMatch(source=key, score=round(score, 3), snippet=snippet))
            matches.sort(key=lambda item: item.score, reverse=True)
            return matches[: self._top_k]
        except Exception:
            return self._lexical_similarity(description, corpus)

    def _lexical_similarity(self, description: str, corpus: Iterable[tuple[str, str]]) -> list[SimilarityMatch]:
        query_tokens = set(token.lower() for token in description.split())
        matches: list[SimilarityMatch] = []
        if not query_tokens:
            return matches
        for key, text in corpus:
            tokens = set(token.lower() for token in text.split())
            intersection = len(query_tokens & tokens)
            union = len(query_tokens | tokens)
            score = intersection / union if union else 0.0
            matches.append(
                SimilarityMatch(source=key, score=round(score, 3), snippet=self._snippet(text))
            )
        matches.sort(key=lambda item: item.score, reverse=True)
        return matches[: self._top_k]

    def _snippet(self, text: str, max_length: int = 120) -> str:
        cleaned = " ".join(text.split())
        return cleaned[:max_length] + ("..." if len(cleaned) > max_length else "")

    # ------------------------------------------------------------------
    # Claim detection & AI-generated heuristics
    def _flag_claims(self, description: str) -> list[ClaimFlag]:
        sentences = [sentence.strip() for sentence in re.split(r"[\.!?]\s+", description) if sentence.strip()]
        keywords = {
            "accuracy",
            "guarantee",
            "perfect",
            "zero",
            "100%",
            "95%",
            "state-of-the-art",
            "breakthrough",
        }
        flags: list[ClaimFlag] = []
        for sentence in sentences:
            numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", sentence)
            lower = sentence.lower()
            if numbers or any(word in lower for word in keywords):
                reason_parts = []
                if numbers:
                    high_numbers = [num for num in numbers if num.endswith("%") and float(num.rstrip("%")) >= 90]
                    if high_numbers:
                        reason_parts.append(f"High success figures: {', '.join(high_numbers)}")
                if "guarantee" in lower or "zero" in lower:
                    reason_parts.append("Potentially absolute claim")
                if "state-of-the-art" in lower or "breakthrough" in lower:
                    reason_parts.append("Marketing language detected")
                if not reason_parts:
                    reason_parts.append("Contains quantifiable claim requiring verification")
                flags.append(ClaimFlag(statement=sentence, reason="; ".join(reason_parts)))
        return flags[: self._top_k]

    def _estimate_ai_generated(self, description: str) -> float:
        description = description.strip()
        if not description:
            return 0.0

        if pipeline and self._ai_detector_model:
            try:  # pragma: no cover - optional dependency
                if self._ai_detector is None:
                    self._ai_detector = pipeline(
                        "text-classification",
                        model=self._ai_detector_model,
                        top_k=None,
                        truncation=True,
                    )
                result = self._ai_detector(description[:4096])
                if isinstance(result, list) and result:
                    entries = result[0] if isinstance(result[0], list) else result
                    ai_score = 0.0
                    for entry in entries:
                        label = entry.get("label", "").lower()
                        score = float(entry.get("score", 0.0))
                        if "ai" in label or "fake" in label:
                            ai_score = max(ai_score, score)
                    if ai_score:
                        return ai_score
            except Exception:
                pass

        # Heuristic fallback: measure repetitiveness and lack of personal pronouns
        tokens = [token.lower() for token in re.findall(r"\b\w+\b", description)]
        if not tokens:
            return 0.0
        pronouns = {"i", "we", "our", "us", "team"}
        pronoun_ratio = sum(token in pronouns for token in tokens) / len(tokens)
        unique_ratio = len(set(tokens)) / len(tokens)
        repetition_score = max(0.0, 1.0 - unique_ratio)
        ai_likelihood = 0.4 * repetition_score + 0.3 * (0.2 - pronoun_ratio)
        return max(0.0, min(1.0, ai_likelihood + 0.3))
