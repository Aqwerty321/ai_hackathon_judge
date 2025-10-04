from ai_judge.utils.evaluation import evaluate_binary


def test_evaluate_binary_perfect_scores() -> None:
    y_true = [1, 1, 0, 0]
    y_scores = [0.9, 0.8, 0.2, 0.1]

    result = evaluate_binary(y_true, y_scores, threshold=0.5, target_tpr=0.95)

    assert result.auroc == 1.0
    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.f1 == 1.0
    assert result.fpr_at_target_tpr == 0.0


def test_evaluate_binary_handles_no_positives_for_precision() -> None:
    y_true = [0, 0, 0]
    y_scores = [0.2, 0.4, 0.8]

    result = evaluate_binary(y_true, y_scores, threshold=0.5, target_tpr=0.95)

    assert result.auroc is None
    assert result.precision == 0.0
    assert result.recall is None
    assert result.f1 is None
    assert result.fpr_at_target_tpr is None
