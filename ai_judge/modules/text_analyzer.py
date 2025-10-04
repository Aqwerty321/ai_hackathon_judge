from __future__ import annotations

import logging
import math
import re
import warnings
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Tuple

from ..utils.file_helpers import read_submission_description, read_text
from ..utils.torch_helpers import DeviceSpec

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

try:  # pragma: no cover - optional dependency
    from ddgs import DDGS  # type: ignore
except ImportError:  # pragma: no cover
    try:
        from duckduckgo_search import DDGS  # type: ignore
    except ImportError:  # pragma: no cover
        DDGS = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None  # type: ignore

if DDGS is not None and getattr(DDGS, "__module__", "").startswith("duckduckgo_search"):
    warnings.filterwarnings(
        "ignore",
        message=r".*duckduckgo_search.*renamed to `ddgs`",
        category=RuntimeWarning,
    )


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
    combined_summary: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "originality_score": self.originality_score,
            "feasibility_score": self.feasibility_score,
            "summary": self.summary,
            "similarity_matches": [match.to_dict() for match in self.similarity_matches],
            "suspect_claims": [claim.to_dict() for claim in self.suspect_claims],
            "ai_generated_likelihood": self.ai_generated_likelihood,
            "combined_summary": self.combined_summary,
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
            combined_summary=data.get("combined_summary"),
        )


class TextAnalyzer:
    """Hybrid text analyzer blending heuristics with optional ML models."""

    def __init__(
        self,
        similarity_corpus_dir: Path | None = None,
        embedding_model: str | None = None,
        top_k: int = 5,
        ai_detector_model: str | None = None,
        ai_detector_context_length: int = 4096,
        device_spec: DeviceSpec | None = None,
        gemini_api_key: str | None = None,
        gemini_model: str = "models/gemini-2.0-flash-lite",
    ) -> None:
        self.similarity_corpus_dir = Path(similarity_corpus_dir) if similarity_corpus_dir else None
        self._embedding_model_name = embedding_model
        self._ai_detector_model = ai_detector_model
        self._top_k = top_k

        self._embedder = None
        self._ai_detector = None
        self._corpus_cache: list[tuple[str, str]] | None = None
        self._device_spec = device_spec
        self._ai_detector_context_length = max(512, ai_detector_context_length)
        self._gemini_api_key = gemini_api_key
        self._gemini_model = gemini_model
        self._gemini_client = None

    def analyze(self, submission_dir: Path, transcript: str = "") -> TextAnalysisResult:
        description, _ = read_submission_description(submission_dir)
        word_count = len(description.split())
        matches = self._compute_similarity(description)
        originality = self._estimate_originality(description, matches)
        feasibility = self._estimate_feasibility(word_count)
        summary = self._summarize(description)
        claims = self._flag_claims(description)
        claims = self._enrich_claims_with_gemini(description, claims)
        claims = self._verify_claims(claims)
        ai_likelihood = self._estimate_ai_generated(description)
        combined_summary = self._generate_combined_summary(description, transcript)

        return TextAnalysisResult(
            originality_score=originality,
            feasibility_score=feasibility,
            summary=summary,
            similarity_matches=tuple(matches),
            suspect_claims=tuple(claims),
            ai_generated_likelihood=round(ai_likelihood, 3),
            combined_summary=combined_summary,
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
                device_kwargs: dict[str, object] = {}
                if self._device_spec is not None:
                    device_kwargs["device"] = self._device_spec.sentence_transformer_device
                self._embedder = SentenceTransformer(self._embedding_model_name, **device_kwargs)
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
        """Flag suspect claims using Gemini AI for intelligent detection."""
        # Try Gemini-powered detection first
        if self._gemini_api_key and genai:
            try:
                return self._flag_claims_with_gemini(description)
            except Exception as exc:
                LOGGER.warning("Gemini claim flagging failed: %s. Falling back to rule-based detection.", exc)
        
        # Fallback: Rule-based detection
        return self._flag_claims_rule_based(description)
    
    def _flag_claims_with_gemini(self, description: str) -> list[ClaimFlag]:
        """Use Gemini AI to intelligently identify suspect claims."""
        # Initialize Gemini client if needed
        if self._gemini_client is None:
            genai.configure(api_key=self._gemini_api_key)
            self._gemini_client = genai.GenerativeModel(self._gemini_model)
        
        # Clean and prepare text
        cleaned_desc = self._clean_text_for_gemini(description)[:3000]
        
        prompt = (
            "You are an expert hackathon judge analyzing project descriptions for suspicious or unverifiable claims.\n\n"
            "Identify statements that:\n"
            "- Make absolute guarantees or promises (e.g., '100% accurate', 'guaranteed', 'never fails')\n"
            "- Claim unusually high success rates (e.g., '99% accuracy', '95% performance')\n"
            "- Use marketing hype without evidence (e.g., 'revolutionary', 'state-of-the-art', 'breakthrough')\n"
            "- Make quantifiable claims that need verification (e.g., specific metrics, benchmarks)\n"
            "- Overstate capabilities or impact\n\n"
            "For each suspect claim, provide:\n"
            "1. The exact statement (quote from text)\n"
            "2. Why it's suspicious (brief reason)\n\n"
            f"Project description:\n{cleaned_desc}\n\n"
            "Output format (one claim per line pair):\n"
            "CLAIM: <exact quote>\n"
            "REASON: <why it's suspicious>\n\n"
            "If no suspicious claims found, respond with: NO_CLAIMS_FOUND\n"
        )
        
        try:
            response = self._gemini_client.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,  # Lower for more precise detection
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 800,
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                    if candidate.content.parts:
                        response_text = candidate.content.parts[0].text.strip()
                        
                        if "NO_CLAIMS_FOUND" in response_text:
                            LOGGER.info("Gemini found no suspicious claims")
                            return []
                        
                        # Parse claims from response
                        flags = self._parse_gemini_claims(response_text)
                        LOGGER.info("Gemini identified %d suspicious claims", len(flags))
                        return flags[:self._top_k]
        except Exception as exc:
            LOGGER.warning("Gemini claim detection failed: %s", exc)
            raise
        
        return []
    
    def _parse_gemini_claims(self, response_text: str) -> list[ClaimFlag]:
        """Parse Gemini's response to extract claims and reasons."""
        flags: list[ClaimFlag] = []
        lines = response_text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for CLAIM: pattern
            if line.upper().startswith('CLAIM:'):
                claim_text = line[6:].strip().strip('"\'')
                reason_text = "AI-detected suspicious claim"
                
                # Look for corresponding REASON: on next lines
                for j in range(i + 1, min(i + 3, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.upper().startswith('REASON:'):
                        reason_text = next_line[7:].strip()
                        i = j
                        break
                
                if claim_text:
                    flags.append(ClaimFlag(statement=claim_text, reason=reason_text))
            
            i += 1
        
        return flags
    
    def _flag_claims_rule_based(self, description: str) -> list[ClaimFlag]:
        """Fallback rule-based claim detection."""
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


    def _enrich_claims_with_gemini(self, description: str, claims: list[ClaimFlag]) -> list[ClaimFlag]:
        """Use Gemini AI to verify and enrich claims."""
        try:
            # Initialize Gemini client if needed
            if self._gemini_client is None:
                genai.configure(api_key=self._gemini_api_key)
                self._gemini_client = genai.GenerativeModel(self._gemini_model)
            
            enriched: list[ClaimFlag] = []
            for idx, claim in enumerate(claims):
                if idx >= self._top_k:
                    enriched.append(claim)
                    continue
                
                # Build prompt for claim verification
                prompt = self._build_claim_prompt(description, claim.statement)
                
                try:
                    response = self._gemini_client.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.2,  # Low for factual analysis
                            "top_p": 0.8,
                            "top_k": 40,
                            "max_output_tokens": 150,
                        },
                        safety_settings=[
                            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                        ]
                    )
                    
                    # Parse response
                    if response and hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                            if candidate.content.parts:
                                response_text = candidate.content.parts[0].text
                                verdict, rationale = self._parse_llm_verdict(response_text)
                                enriched.append(replace(claim, llm_verdict=verdict, llm_rationale=rationale))
                                continue
                except Exception as exc:
                    LOGGER.debug("Gemini claim verification failed for '%s': %s", claim.statement[:50], exc)
                
                # Fallback: keep claim without enrichment
                enriched.append(claim)
            
            LOGGER.info("Enriched %d claims using Gemini AI", len([c for c in enriched if c.llm_verdict]))
            return enriched
            
        except Exception as exc:
            LOGGER.warning("Gemini claim enrichment failed: %s", exc)
            return claims

    def _build_claim_prompt(self, description: str, claim: str) -> str:
        # Truncate description to reasonable length for Gemini context
        description = (description.strip() or "No description provided.")[:2000]
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

        # Try Gemini first for most accurate detection
        gemini_score = self._estimate_ai_with_gemini(description)
        if gemini_score is not None:
            return gemini_score

        if pipeline and self._ai_detector_model:
            try:  # pragma: no cover - optional dependency
                if self._ai_detector is None:
                    pipeline_kwargs: dict[str, object] = {
                        "model": self._ai_detector_model,
                        "top_k": None,
                        "truncation": True,
                    }
                    if self._device_spec is not None:
                        pipeline_kwargs["device"] = self._device_spec.pipeline_device
                    self._ai_detector = pipeline("text-classification", **pipeline_kwargs)
                truncated = description[: self._ai_detector_context_length]
                result = self._ai_detector(truncated)
                if isinstance(result, list) and result:
                    entries = result[0] if isinstance(result[0], list) else result
                    ai_score = 0.0
                    for entry in entries:
                        label = entry.get("label", "").lower()
                        score = float(entry.get("score", 0.0))
                        if "ai" in label or "fake" in label:
                            ai_score = max(ai_score, score)
                    if ai_score > 0.1:  # Only return if confident
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

    def _estimate_ai_with_gemini(self, text: str) -> float | None:
        """Use Gemini to detect AI-generated content with high accuracy."""
        if not self._gemini_api_key or not genai:
            return None
        
        try:
            # Limit text length to avoid context overflow
            max_chars = 4000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            # Initialize Gemini if needed
            if not hasattr(self, '_gemini_ai_detector'):
                genai.configure(api_key=self._gemini_api_key)
                self._gemini_ai_detector = genai.GenerativeModel(self._gemini_model)
            
            prompt = f"""Analyze the following text and determine the likelihood it was written by AI (like ChatGPT, Claude, Gemini, etc.) versus a human.

Consider these indicators:
- **AI indicators**: Perfect grammar, overly formal tone, generic phrasing, repetitive structure, lack of personal voice, buzzword-heavy, no typos/colloquialisms
- **Human indicators**: Personal anecdotes, casual language, minor errors, unique voice, authentic enthusiasm, specific details, conversational flow

Text to analyze:
```
{text}
```

Respond with ONLY a JSON object in this exact format:
{{
  "likelihood": 0.X,
  "confidence": "high|medium|low",
  "reasoning": "brief 1-2 sentence explanation"
}}

Where likelihood is a decimal from 0.0 (definitely human) to 1.0 (definitely AI).
Examples:
- 0.9-1.0: Almost certainly AI (perfect, generic, corporate-speak)
- 0.7-0.8: Likely AI (polished but lacks personality)
- 0.4-0.6: Mixed or uncertain (could be either)
- 0.2-0.3: Likely human (personal, casual, imperfect)
- 0.0-0.1: Almost certainly human (very personal, unique voice)"""

            response = self._gemini_ai_detector.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,  # Lower temperature for consistent analysis
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 200,
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                    if candidate.content.parts:
                        result_text = candidate.content.parts[0].text.strip()
                        
                        # Try to parse JSON response
                        try:
                            # Extract JSON from markdown code blocks if present
                            if "```json" in result_text:
                                result_text = result_text.split("```json")[1].split("```")[0].strip()
                            elif "```" in result_text:
                                result_text = result_text.split("```")[1].split("```")[0].strip()
                            
                            import json
                            result = json.loads(result_text)
                            likelihood = float(result.get("likelihood", 0.5))
                            confidence = result.get("confidence", "medium")
                            reasoning = result.get("reasoning", "")
                            
                            LOGGER.info("✓ Gemini AI detection: likelihood=%.2f (%s confidence) - %s", 
                                       likelihood, confidence, reasoning[:100])
                            
                            return max(0.0, min(1.0, likelihood))
                        except (json.JSONDecodeError, ValueError) as e:
                            LOGGER.warning("Failed to parse Gemini AI detection response: %s", e)
                            # Try to extract likelihood from text if JSON parsing fails
                            import re
                            match = re.search(r'"likelihood":\s*([0-9.]+)', result_text)
                            if match:
                                return float(match.group(1))
        
        except Exception as exc:
            LOGGER.warning("Gemini AI detection failed: %s", exc)
        
        return None

    def _generate_combined_summary(self, description: str, transcript: str) -> str | None:
        """Generate an AI-powered summary combining README and video transcript.
        
        Priority order:
        1. Gemini Pro API (if API key provided)
        2. Local BART model (facebook/bart-large-cnn)
        """
        # Merge description and transcript
        combined = self._merge_texts(description, transcript)
        if not combined.strip():
            return None

        # PRIORITY 1: Try Gemini Pro API first
        if self._gemini_api_key and genai:
            try:
                summary = self._generate_summary_with_gemini(combined)
                if summary:
                    LOGGER.info("Generated combined summary using Gemini Pro API")
                    return summary
            except Exception as exc:
                LOGGER.warning("Gemini API summary generation failed: %s", exc)

        # No fallback - Gemini-only for AI-powered summaries
        LOGGER.warning("Gemini API not configured or failed; no combined summary available.")
        return None

    def _generate_summary_with_gemini(self, text: str) -> str | None:
        """Generate summary using Google Gemini Pro API."""
        if not genai or not self._gemini_api_key:
            return None

        try:
            # Initialize Gemini client if not already done
            if self._gemini_client is None:
                genai.configure(api_key=self._gemini_api_key)
                self._gemini_client = genai.GenerativeModel(self._gemini_model)

            # Clean and prepare text to avoid RECITATION filtering
            cleaned_text = self._clean_text_for_gemini(text)
            
            # Craft a more instructive prompt that encourages original phrasing
            prompt = f"""Analyze this hackathon project and write a comprehensive ORIGINAL summary in your own words (4-6 sentences). 
Do NOT copy phrases from the input. Paraphrase and synthesize the key information about:
- What specific problem does it solve and why is it important?
- What are the main technical features and capabilities?
- What technologies, languages, and frameworks are used?
- What makes this project innovative or interesting?
- What is the target use case or audience?

Project Information:
{cleaned_text}

Write a detailed, fresh, original summary now:"""

            # Generate summary with higher temperature to encourage original phrasing
            response = self._gemini_client.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,  # Higher = more creative/original
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 400,  # Increased for longer summaries
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )

            # Check if response is valid
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Check if generation completed successfully
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                    if candidate.content.parts:
                        summary = candidate.content.parts[0].text.strip()
                        # Clean up any potential markdown formatting
                        summary = re.sub(r'^#+\s*', '', summary)
                        summary = re.sub(r'\*\*([^*]+)\*\*', r'\1', summary)
                        if summary:
                            LOGGER.info("Generated combined summary using Gemini Pro API")
                            return summary
                
                # If we got here, response was blocked or empty
                finish_reason = getattr(candidate, 'finish_reason', 'UNKNOWN')
                LOGGER.warning("Gemini response blocked or empty (finish_reason=%s)", finish_reason)

        except Exception as exc:
            LOGGER.warning("Gemini API call failed: %s", exc)

        return None

    def _clean_text_for_gemini(self, text: str) -> str:
        """Clean and prepare text to reduce RECITATION filtering triggers."""
        # Remove emojis and special unicode characters
        cleaned = re.sub(r'[^\x00-\x7F]+', ' ', text)
        
        # Remove markdown formatting
        cleaned = re.sub(r'#+\s*', '', cleaned)  # Headers
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)  # Bold
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)  # Italic
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)  # Code
        
        # Remove URLs to reduce training data matches
        cleaned = re.sub(r'https?://[^\s]+', '', cleaned)
        
        # Remove common tutorial boilerplate phrases
        cleaned = re.sub(r'(Clone the Repository|Getting Started|Installation|How to Run)', '', cleaned, flags=re.IGNORECASE)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Truncate to avoid overwhelming (keep first 2000 chars)
        if len(cleaned) > 2000:
            cleaned = cleaned[:2000] + "..."
        
        return cleaned.strip()

    def _merge_texts(self, description: str, transcript: str) -> str:
        """Combine description and transcript intelligently."""
        parts = []

        desc_clean = description.strip()
        if desc_clean:
            parts.append(f"Project Description: {desc_clean}")

        trans_clean = transcript.strip()
        if trans_clean:
            parts.append(f"Presentation Transcript: {trans_clean}")

        return "\n\n".join(parts)
