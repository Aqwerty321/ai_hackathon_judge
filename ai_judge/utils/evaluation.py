from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class BinaryEvalResult:
    """Stores classification reliability metrics for judge score calibration."""

    auroc: float | None
    precision: float | None
    recall: float | None
    f1: float | None
    threshold: float
    roc_curve: Tuple[Tuple[float, float], ...]
    pr_curve: Tuple[Tuple[float, float], ...]
    fpr_at_target_tpr: float | None
    target_tpr: float


def evaluate_binary(
    y_true: Sequence[int],
    y_scores: Sequence[float],
    threshold: float = 0.5,
    target_tpr: float = 0.95,
) -> BinaryEvalResult:
    """Evaluate prediction scores against binary labels.

    Args:
        y_true: Iterable containing 0/1 integer labels.
        y_scores: Iterable containing prediction scores (higher is more positive).
        threshold: Score threshold used to derive precision/recall/F1.
        target_tpr: Desired true positive rate used to compute FPR@target.

    Returns:
        BinaryEvalResult with ROC, PR, AUROC, precision/recall/F1, and FPR@target.

    Raises:
        ValueError: if the inputs are empty or of mismatched lengths.
    """

    labels = list(int(label) for label in y_true)
    scores = list(float(score) for score in y_scores)
    if not labels:
        raise ValueError("Inputs must not be empty.")
    if len(labels) != len(scores):
        raise ValueError("Labels and scores must have the same length.")
    if any(label not in (0, 1) for label in labels):
        raise ValueError("Labels must be binary (0 or 1).")

    positives = sum(labels)
    negatives = len(labels) - positives
    degenerate = positives == 0 or negatives == 0

    roc_curve = _roc_curve(labels, scores)
    auroc = None if degenerate else _area_under_curve(roc_curve)

    pr_curve = _precision_recall_curve(labels, scores)
    precision, recall, f1 = _summary_at_threshold(labels, scores, threshold)

    fpr_target = None if degenerate else _fpr_at_target_tpr(labels, scores, target_tpr)

    return BinaryEvalResult(
        auroc=auroc,
        precision=precision,
        recall=recall,
        f1=f1,
        threshold=threshold,
        roc_curve=tuple(roc_curve),
        pr_curve=tuple(pr_curve),
        fpr_at_target_tpr=fpr_target,
        target_tpr=target_tpr,
    )


def _roc_curve(labels: Sequence[int], scores: Sequence[float]) -> List[Tuple[float, float]]:
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return [(0.0, 0.0), (1.0, 1.0)]

    sorted_pairs = sorted(zip(scores, labels), key=lambda item: item[0], reverse=True)
    tp = fp = 0
    roc_points: List[Tuple[float, float]] = [(0.0, 0.0)]
    last_score = None
    for score, label in sorted_pairs:
        if last_score is not None and score != last_score:
            roc_points.append((fp / negatives, tp / positives))
        if label == 1:
            tp += 1
        else:
            fp += 1
        last_score = score
    roc_points.append((fp / negatives if negatives else 1.0, tp / positives if positives else 1.0))
    if roc_points[-1] != (1.0, 1.0):
        roc_points.append((1.0, 1.0))
    return roc_points


def _precision_recall_curve(labels: Sequence[int], scores: Sequence[float]) -> List[Tuple[float, float]]:
    positives = sum(labels)
    if positives == 0:
        return [(1.0, 0.0)]

    sorted_pairs = sorted(zip(scores, labels), key=lambda item: item[0], reverse=True)
    tp = fp = 0
    points: List[Tuple[float, float]] = []
    for score, label in sorted_pairs:
        if label == 1:
            tp += 1
        else:
            fp += 1
        precision = tp / (tp + fp)
        recall = tp / positives
        points.append((recall, precision))
    points.insert(0, (0.0, 1.0))
    return points


def _area_under_curve(points: Iterable[Tuple[float, float]]) -> float:
    ordered = list(points)
    if len(ordered) < 2:
        return 0.0
    area = 0.0
    for (x0, y0), (x1, y1) in zip(ordered[:-1], ordered[1:]):
        width = max(x1 - x0, 0.0)
        area += width * (y0 + y1) / 2
    return round(area, 6)


def _summary_at_threshold(
    labels: Sequence[int], scores: Sequence[float], threshold: float
) -> Tuple[float | None, float | None, float | None]:
    tp = fp = tn = fn = 0
    for label, score in zip(labels, scores):
        prediction = 1 if score >= threshold else 0
        if prediction == 1 and label == 1:
            tp += 1
        elif prediction == 1 and label == 0:
            fp += 1
        elif prediction == 0 and label == 0:
            tn += 1
        else:
            fn += 1
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    if precision is None or recall is None or (precision + recall) == 0:
        f1 = None
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return (
        round(precision, 6) if precision is not None else None,
        round(recall, 6) if recall is not None else None,
        round(f1, 6) if f1 is not None else None,
    )


def _fpr_at_target_tpr(
    labels: Sequence[int], scores: Sequence[float], target_tpr: float
) -> float | None:
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None

    sorted_pairs = sorted(zip(scores, labels), key=lambda item: item[0], reverse=True)
    tp = fp = 0
    best_fpr: float | None = None
    for score, label in sorted_pairs:
        if label == 1:
            tp += 1
        else:
            fp += 1
        tpr = tp / positives
        fpr = fp / negatives
        if tpr >= target_tpr:
            if best_fpr is None or fpr < best_fpr:
                best_fpr = fpr
    return round(best_fpr, 6) if best_fpr is not None else None
