"""Classification + probabilistic metrics used by the backtesting engine
and Model Lab: accuracy, per-class precision/recall/F1, confusion matrix,
multi-class Brier score, log loss, and calibration curve/error.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from sklearn.metrics import confusion_matrix as sk_confusion_matrix
from sklearn.metrics import precision_recall_fscore_support

OUTCOMES = ("HOME", "DRAW", "AWAY")
LOG_LOSS_EPSILON = 1e-6
CALIBRATION_BUCKET_SIZE = 0.1


@dataclass
class ClassificationReport:
    accuracy: float
    precision: dict[str, float]
    recall: dict[str, float]
    f1: dict[str, float]
    confusion_matrix: list[list[int]]
    labels: list[str]

    def as_dict(self) -> dict:
        return {
            "accuracy": round(self.accuracy, 4),
            "precision": {k: round(v, 4) for k, v in self.precision.items()},
            "recall": {k: round(v, 4) for k, v in self.recall.items()},
            "f1": {k: round(v, 4) for k, v in self.f1.items()},
            "confusion_matrix": self.confusion_matrix,
            "labels": self.labels,
        }


def classification_report(y_true: list[str], y_pred: list[str]) -> ClassificationReport | None:
    if not y_true:
        return None

    labels = list(OUTCOMES)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    matrix = sk_confusion_matrix(y_true, y_pred, labels=labels)
    accuracy = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == p) / len(y_true)

    return ClassificationReport(
        accuracy=accuracy,
        precision=dict(zip(labels, precision, strict=True)),
        recall=dict(zip(labels, recall, strict=True)),
        f1=dict(zip(labels, f1, strict=True)),
        confusion_matrix=matrix.tolist(),
        labels=labels,
    )


def outcome_vector(outcome: str) -> tuple[float, float, float]:
    return {
        "HOME": (1.0, 0.0, 0.0),
        "DRAW": (0.0, 1.0, 0.0),
        "AWAY": (0.0, 0.0, 1.0),
    }[outcome]


def brier_score(predicted: tuple[float, float, float], actual_outcome: str) -> float:
    actual = outcome_vector(actual_outcome)
    return sum((p - a) ** 2 for p, a in zip(predicted, actual, strict=True))


def log_loss_single(predicted: tuple[float, float, float], actual_outcome: str) -> float:
    index = OUTCOMES.index(actual_outcome)
    return -math.log(max(predicted[index], LOG_LOSS_EPSILON))


@dataclass
class CalibrationPoint:
    predicted_range: str
    matches: int
    mean_predicted: float
    actual_frequency: float

    def as_dict(self) -> dict:
        return {
            "predicted_range": self.predicted_range,
            "matches": self.matches,
            "mean_predicted": round(self.mean_predicted, 4),
            "actual_frequency": round(self.actual_frequency, 4),
        }


def calibration_curve(samples: list[tuple[float, bool]]) -> list[CalibrationPoint]:
    """``samples``: (predicted_probability, was_correct) for the model's own
    favourite outcome in each match."""
    buckets: dict[int, list[tuple[float, bool]]] = {}
    n_buckets = round(1 / CALIBRATION_BUCKET_SIZE)
    for predicted, correct in samples:
        bucket = min(int(predicted / CALIBRATION_BUCKET_SIZE), n_buckets - 1)
        buckets.setdefault(bucket, []).append((predicted, correct))

    points = []
    for bucket in sorted(buckets):
        entries = buckets[bucket]
        points.append(
            CalibrationPoint(
                predicted_range=f"{bucket * CALIBRATION_BUCKET_SIZE:.0%}-{(bucket + 1) * CALIBRATION_BUCKET_SIZE:.0%}",
                matches=len(entries),
                mean_predicted=sum(p for p, _ in entries) / len(entries),
                actual_frequency=sum(1 for _, c in entries if c) / len(entries),
            )
        )
    return points


def calibration_error(points: list[CalibrationPoint], total_samples: int) -> float | None:
    """Expected Calibration Error (ECE): the weighted average gap between
    predicted probability and observed frequency across buckets."""
    if not points or not total_samples:
        return None
    return sum(
        (p.matches / total_samples) * abs(p.mean_predicted - p.actual_frequency) for p in points
    )
