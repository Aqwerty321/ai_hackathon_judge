from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Tuple

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

try:  # pragma: no cover - optional heavy dependencies
    from ctransformers import AutoModelForCausalLM  # type: ignore
except ImportError:  # pragma: no cover - optional heavy dependencies
    AutoModelForCausalLM = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from duckduckgo_search import DDGS  # type: ignore
except ImportError:  # pragma: no cover
    DDGS = None  # type: ignore


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SimilarityMatch:
    """Top-k similarity result from the reference corpus."""

    source: str
    score: float
    snippet: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "score": self.score,
            "snippet": self.snippet,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SimilarityMatch":
        return cls(
            source=str(data.get("source", "")),
            score=float(data.get("score", 0.0)),
            snippet=str(data.get("snippet", "")),
        )


@dataclass(frozen=True)
class ClaimVerificationResult:
    """Outcome of lightweight external fact-checking for a claim."""

    status: str
    note: str | None = None
    evidence: Tuple[Mapping[str, str], ...] = tuple()

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "note": self.note,
            "evidence": [dict(item) for item in self.evidence],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ClaimVerificationResult":
        evidence_items: list[Mapping[str, str]] = []
        for item in data.get("evidence", []):
            if isinstance(item, Mapping):
                evidence_items.append(
                    {
                        "title": str(item.get("title", "")),
                        "url": str(item.get("url", "")),
                        "snippet": str(item.get("snippet", "")),
                    }
                )
        return cls(
            status=str(data.get("status", "")),
            note=(data.get("note") if data.get("note") is not None else None),
            evidence=tuple(evidence_items),
        )


@dataclass(frozen=True)
class ClaimFlag:
    """Represents a potentially exaggerated or unverifiable claim."""

    statement: str
    reason: str
    llm_verdict: str | None = None
    llm_rationale: str | None = None
    verification_result: ClaimVerificationResult | None = None

    def to_dict(self) -> dict[str, object]:
        verification_dict = (
            self.verification_result.to_dict() if self.verification_result is not None else None
        )
        return {
            "statement": self.statement,
            "reason": self.reason,
            "llm_verdict": self.llm_verdict,
            "llm_rationale": self.llm_rationale,
            "verification_result": verification_dict,
            # Backwards compatibility with cached results
            "verification_status": (
                verification_dict.get("status") if verification_dict else None
            ),
            "verification_evidence": (
                [item.get("snippet", "") for item in verification_dict.get("evidence", [])]
                if verification_dict
                else []
            ),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ClaimFlag":
        verification_result: ClaimVerificationResult | None = None
        verification_payload = data.get("verification_result")
        if isinstance(verification_payload, Mapping):
            verification_result = ClaimVerificationResult.from_dict(verification_payload)
        else:
            status = data.get("verification_status")
            evidence = [item for item in data.get("verification_evidence", []) if isinstance(item, str)]
            if status or evidence:
                verification_result = ClaimVerificationResult(
                    status=str(status) if status else "needs_review",
                    note=None,
                    evidence=tuple(
                        {
                            "title": "",
                            "url": "",
                            "snippet": snippet,
                        }
                        for snippet in evidence
                    ),
                )
        return cls(
            statement=str(data.get("statement", "")),
            reason=str(data.get("reason", "")),
            llm_verdict=(data.get("llm_verdict") if data.get("llm_verdict") is not None else None),
            llm_rationale=(
                data.get("llm_rationale") if data.get("llm_rationale") is not None else None
            ),
            verification_result=verification_result,
        )


@dataclass(frozen=True)
class TextAnalysisResult:
    """Results of analyzing the written project description."""

    originality_score: float
    feasibility_score: float
    summary: str
    similarity_matches: Tuple[SimilarityMatch, ...]
    suspect_claims: Tuple[ClaimFlag, ...]
    ai_generated_likelihood: float

    def to_dict(self) -> dict[str, object]:
        return {
            "originality_score": self.originality_score,
            "feasibility_score": self.feasibility_score,
            "summary": self.summary,
            "similarity_matches": [match.to_dict() for match in self.similarity_matches],
            "suspect_claims": [claim.to_dict() for claim in self.suspect_claims],
            "ai_generated_likelihood": self.ai_generated_likelihood,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TextAnalysisResult":
        matches = tuple(
            SimilarityMatch.from_dict(item)
            for item in data.get("similarity_matches", [])
            if isinstance(item, Mapping)
        )
        claims = tuple(
            ClaimFlag.from_dict(item)
            for item in data.get("suspect_claims", [])
            if isinstance(item, Mapping)
        )
        return cls(
            originality_score=float(data.get("originality_score", 0.0)),
            feasibility_score=float(data.get("feasibility_score", 0.0)),
            summary=str(data.get("summary", "")),
            similarity_matches=matches,
            suspect_claims=claims,
            ai_generated_likelihood=float(data.get("ai_generated_likelihood", 0.0)),
        )


class TextAnalyzer:
    """Hybrid text analyzer blending heuristics with optional ML models."""

    def __init__(
        self,
        similarity_corpus_dir: Path | None = None,
        intermediate_dir: Path | None = None,
        embedding_model: str | None = None,
        top_k: int = 5,
        ai_detector_model: str | None = None,
        llm_model_path: Path | None = None,
        llm_model_type: str = "auto",
        llm_max_tokens: int = 256,
    ) -> None:
        self.similarity_corpus_dir = Path(similarity_corpus_dir) if similarity_corpus_dir else None
        self._cache_dir = Path(intermediate_dir) if intermediate_dir else None
        if self._cache_dir:
            ensure_directory(self._cache_dir)
        self._embedding_model_name = embedding_model
        self._ai_detector_model = ai_detector_model
        self._top_k = top_k
        self._llm_model_path = Path(llm_model_path) if llm_model_path else None
        self._llm_model_type = llm_model_type
        self._llm_max_tokens = llm_max_tokens

        self._embedder = None
        self._ai_detector = None
        self._corpus_cache: list[tuple[str, str]] | None = None
        self._llm = None

    def analyze(self, submission_dir: Path) -> TextAnalysisResult:
        description = read_text(submission_dir / "description.txt")
        word_count = len(description.split())
        matches = self._compute_similarity(description)
        originality = self._estimate_originality(description, matches)
        feasibility = self._estimate_feasibility(word_count)
        summary = self._summarize(description)
        claims = self._flag_claims(description)
        claims = self._enrich_claims_with_llm(description, claims)
        claims = self._verify_claims(claims)
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

    # ------------------------------------------------------------------
    # Claim verification
    def _verify_claims(self, claims: Sequence[ClaimFlag]) -> Tuple[ClaimFlag, ...]:
        if not claims:
            return tuple()

        verified: list[ClaimFlag] = []
        for claim in claims:
            evidence = self._search_evidence(claim.statement)
            verification_result = self._derive_verification_result(claim.statement, evidence)
            verified.append(replace(claim, verification_result=verification_result))
        return tuple(verified)

    def _search_evidence(self, query: str, max_results: int = 3) -> list[Mapping[str, Any]]:
        if DDGS is None:
            return []
        try:  # pragma: no cover - network dependent
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=max_results)
                return list(results)
        except Exception as exc:  # pragma: no cover
            LOGGER.debug("Claim verification search failed: %s", exc)
            return []

    def _derive_verification_result(
        self, statement: str, evidence: Iterable[Mapping[str, Any]]
    ) -> ClaimVerificationResult | None:
        normalized_evidence: list[Mapping[str, str]] = []
        statement_tokens = {
            token
            for token in re.findall(r"[a-zA-Z0-9%]+", statement.lower())
            if len(token) > 3
        }
        support_hits = 0
        for entry in evidence:
            snippet = str(
                entry.get("body")
                or entry.get("snippet")
                or entry.get("description")
                or entry.get("title")
                or ""
            ).strip()
            if not snippet:
                continue
            haystack_tokens = set(re.findall(r"[a-zA-Z0-9%]+", snippet.lower()))
            if statement_tokens:
                overlap = len(statement_tokens & haystack_tokens) / len(statement_tokens)
                if overlap >= 0.25:
                    support_hits += 1
            normalized_evidence.append(
                {
                    "title": str(entry.get("title", "")),
                    "url": str(entry.get("href") or entry.get("url") or ""),
                    "snippet": snippet,
                }
            )

        if not normalized_evidence:
            return None

        if support_hits:
            status = "verified"
            note = f"Found {support_hits} supporting source(s)."
        else:
            status = "needs_review"
            note = "No clear supporting evidence found; manual review recommended."

        return ClaimVerificationResult(
            status=status,
            note=note,
            evidence=tuple(normalized_evidence[:3]),
        )

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

    # ------------------------------------------------------------------
    # Local LLM enrichment
    def _enrich_claims_with_llm(self, description: str, claims: list[ClaimFlag]) -> list[ClaimFlag]:
        if not claims or self._llm_model_path is None:
            return claims
        if not self._llm_model_path.exists():
            LOGGER.warning("LLM model path '%s' not found; skipping claim verification.", self._llm_model_path)
            return claims
        if AutoModelForCausalLM is None:
            LOGGER.warning("ctransformers is not installed; skipping local LLM verification.")
            return claims

        if self._llm is None:
            try:  # pragma: no cover - heavy dependency
                self._llm = AutoModelForCausalLM.from_pretrained(
                    str(self._llm_model_path),
                    model_type=self._llm_model_type,
                )
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("Failed to load local LLM from '%s': %s", self._llm_model_path, exc)
                return claims

        enriched: list[ClaimFlag] = []
        for idx, claim in enumerate(claims):
            if idx >= self._top_k:
                enriched.append(claim)
                continue
            prompt = self._build_claim_prompt(description, claim.statement)
            try:  # pragma: no cover - heavy dependency
                response = self._llm(
                    prompt,
                    max_new_tokens=self._llm_max_tokens,
                    temperature=0.1,
                )
            except Exception as exc:
                LOGGER.debug("Local LLM generation failed: %s", exc)
                enriched.append(claim)
                continue
            verdict, rationale = self._parse_llm_verdict(response)
            enriched.append(replace(claim, llm_verdict=verdict, llm_rationale=rationale))
        return enriched

    def _build_claim_prompt(self, description: str, claim: str) -> str:
        description = description.strip() or "No description provided."
        claim = claim.strip()
        return (
            "You are an impartial hackathon judge verifying factual claims.\n"
            "Rate the claim as one of: plausible, needs_verification, implausible.\n"
            "Provide a short reason.\n\n"
            f"Project description:\n{description}\n\n"
            f"Claim: \"{claim}\"\n\n"
            "Respond with two lines exactly:\n"
            "Verdict: <one word>\n"
            "Reason: <explanation up to 25 words>\n"
        )

    def _parse_llm_verdict(self, response: str) -> Tuple[str, str]:
        if not response:
            return "needs_verification", "Local LLM returned empty response."
        verdict_match = re.search(
            r"verdict\s*:\s*(plausible|needs_verification|implausible)",
            response,
            re.IGNORECASE,
        )
        verdict = verdict_match.group(1).lower() if verdict_match else "needs_verification"
        reason_match = re.search(r"reason\s*:\s*(.+)", response, re.IGNORECASE)
        rationale = reason_match.group(1).strip() if reason_match else response.strip()[:160]
        return verdict, rationale

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
