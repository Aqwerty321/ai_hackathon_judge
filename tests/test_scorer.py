import pytest

from ai_judge.modules.code_analyzer import CodeAnalysisResult
from ai_judge.modules.text_analyzer import TextAnalysisResult
from ai_judge.modules.video_analyzer import VideoAnalysisResult
from ai_judge.scoring.criteria import JudgingCriteria
from ai_judge.scoring.scorer import Scorer


def test_score_combination_uses_weights() -> None:
    criteria = JudgingCriteria.from_sequence(
        [
            {
                "key": "presentation",
                "label": "Presentation",
                "weight": 0.4,
                "source": "video.clarity_score",
            },
            {
                "key": "code_quality",
                "label": "Code Quality",
                "weight": 0.6,
                "source": "code.quality_index",
            },
        ]
    )
    scorer = Scorer(criteria)

    video_result = VideoAnalysisResult(
        transcript="Test transcript.",
        clarity_score=0.8,
        estimated_duration_seconds=90.0,
        sentiment_label="positive",
        sentiment_score=0.75,
        transcription_source="unit_test",
    )
    text_result = TextAnalysisResult(
        originality_score=0.7,
        feasibility_score=0.9,
        summary="Summary",
        similarity_matches=tuple(),
        suspect_claims=tuple(),
        ai_generated_likelihood=0.1,
    )
    code_result = CodeAnalysisResult(
        readability_score=0.6, documentation_score=0.8, test_coverage_score_estimate=0.5
    )

    breakdown = scorer.score(video_result, text_result, code_result)

    scores = breakdown.criteria_by_key()
    presentation = scores["presentation"]
    code_quality = scores["code_quality"]

    expected_quality = round((0.6 + 0.8 + 0.5) / 3, 3)
    assert code_quality.raw_value == expected_quality
    assert presentation.normalized_weight == 0.4
    assert code_quality.normalized_weight == 0.6
    weighted_sum = sum(item.weighted_score for item in breakdown.criteria)
    assert breakdown.total == pytest.approx(weighted_sum, rel=1e-6)
    assert 0.0 <= breakdown.total <= 1.0
