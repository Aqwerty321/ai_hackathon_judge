from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import pandas as pd

from ai_judge.utils.evaluation import BinaryEvalResult, evaluate_binary


def _load_scores(frame: pd.DataFrame, score_column: str) -> Sequence[float]:
    if score_column not in frame.columns:
        raise KeyError(f"Column '{score_column}' not present in file. Available columns: {list(frame.columns)}")
    return frame[score_column].astype(float).tolist()


def _load_labels(frame: pd.DataFrame, label_column: str) -> Sequence[int]:
    if label_column not in frame.columns:
        raise KeyError(
            f"Column '{label_column}' not present in file. Available columns: {list(frame.columns)}"
        )
    labels = frame[label_column].astype(int).tolist()
    if any(label not in (0, 1) for label in labels):
        raise ValueError("Ground-truth labels must be 0 or 1")
    return labels


def evaluate_file(
    csv_path: Path,
    score_column: str,
    label_column: str,
    threshold: float,
    target_tpr: float,
) -> BinaryEvalResult:
    frame = pd.read_csv(csv_path)
    scores = _load_scores(frame, score_column)
    labels = _load_labels(frame, label_column)
    return evaluate_binary(labels, scores, threshold=threshold, target_tpr=target_tpr)


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate leaderboard scores against human judgements. "
            "Accepts a CSV containing prediction scores and human-labelled outcomes."
        )
    )
    parser.add_argument("csv", type=Path, help="Path to CSV containing predictions and labels.")
    parser.add_argument(
        "--score-column",
        default="score_total",
        help="Column name containing model scores (default: score_total)",
    )
    parser.add_argument(
        "--label-column",
        default="human_label",
        help="Column name containing binary human labels (default: human_label)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Threshold applied to scores when computing precision/recall/F1 (default: 0.5)",
    )
    parser.add_argument(
        "--target-tpr",
        type=float,
        default=0.95,
        help="Target true-positive rate used for FPR@TPR metric (default: 0.95)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_cli()
    args = parser.parse_args(argv)

    try:
        result = evaluate_file(
            args.csv,
            score_column=args.score_column,
            label_column=args.label_column,
            threshold=args.threshold,
            target_tpr=args.target_tpr,
        )
    except Exception as exc:  # pragma: no cover - CLI guard
        parser.error(str(exc))

    print(f"Evaluated {args.csv}")
    print(f"Threshold: {result.threshold:.3f}")
    if result.auroc is not None:
        print(f"AUROC: {result.auroc:.4f}")
    else:
        print("AUROC: n/a (requires at least one positive and negative label)")
    if result.precision is not None:
        print(f"Precision: {result.precision:.4f}")
    else:
        print("Precision: n/a")
    if result.recall is not None:
        print(f"Recall: {result.recall:.4f}")
    else:
        print("Recall: n/a")
    if result.f1 is not None:
        print(f"F1: {result.f1:.4f}")
    else:
        print("F1: n/a")
    if result.fpr_at_target_tpr is not None:
        print(f"FPR@TPR{int(result.target_tpr * 100)}: {result.fpr_at_target_tpr:.4f}")
    else:
        print(f"FPR@TPR{int(result.target_tpr * 100)}: n/a")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
