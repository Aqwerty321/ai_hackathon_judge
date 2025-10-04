from ai_judge.modules.code_analyzer import CodeAnalysisResult
from ai_judge.modules.text_analyzer import (
    ClaimFlag,
    ClaimVerificationResult,
    SimilarityMatch,
    TextAnalysisResult,
)
from ai_judge.modules.video_analyzer import VideoAnalysisResult


def test_video_analysis_roundtrip() -> None:
    original = VideoAnalysisResult(
        transcript="Sample transcript",
        clarity_score=0.75,
        estimated_duration_seconds=88.5,
        sentiment_label="neutral",
        sentiment_score=0.5,
        transcription_source="cache",
    )
    restored = VideoAnalysisResult.from_dict(original.to_dict())
    assert restored == original


def test_text_analysis_roundtrip() -> None:
    matches = (
        SimilarityMatch(source="ref", score=0.5, snippet="excerpt"),
    )
    claims = (
        ClaimFlag(
            statement="claim",
            reason="reason",
            llm_verdict="plausible",
            llm_rationale="ok",
            verification_result=ClaimVerificationResult(
                status="verified",
                note="Confirmed against trusted source",
                evidence=(
                    {
                        "title": "Trusted Source",
                        "url": "https://example.com",
                        "snippet": "This snippet confirms the claim.",
                    },
                ),
            ),
        ),
    )
    original = TextAnalysisResult(
        originality_score=0.8,
        feasibility_score=0.7,
        summary="Summary text",
        similarity_matches=matches,
        suspect_claims=claims,
        ai_generated_likelihood=0.2,
    )
    restored = TextAnalysisResult.from_dict(original.to_dict())
    assert restored == original


def test_code_analysis_roundtrip() -> None:
    original = CodeAnalysisResult(
        readability_score=0.6,
        documentation_score=0.5,
        test_coverage_score_estimate=0.4,
        details={"lint": {"status": "ok"}},
    )
    restored = CodeAnalysisResult.from_dict(original.to_dict())
    assert restored == original
