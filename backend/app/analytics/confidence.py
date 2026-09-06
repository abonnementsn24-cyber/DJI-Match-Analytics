"""Confidence index (§10 of the product brief): never just "the highest
probability". Combines the gap between the top two outcomes, how much
historical data backs the estimate, how much the four model variants
agree with each other, and — when we have it — the model's own historical
calibration error on this kind of match.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass

from ..core.config import get_settings
from ..models.enums import Confidence

_THRESHOLDS = [
    (0.2, Confidence.VERY_LOW),
    (0.4, Confidence.LOW),
    (0.6, Confidence.MEDIUM),
    (0.8, Confidence.HIGH),
]


@dataclass
class ConfidenceInputs:
    probabilities: tuple[float, float, float]  # (home, draw, away)
    matches_played_min: int
    model_home_win_probabilities: list[float]  # one per model variant, for agreement
    calibration_error: float | None = None  # from model_metrics, lower is better; None if unknown


def _probability_gap_score(probabilities: tuple[float, float, float]) -> float:
    ordered = sorted(probabilities, reverse=True)
    gap = ordered[0] - ordered[1]
    return min(1.0, gap / 0.4)


def _data_volume_score(matches_played_min: int) -> float:
    saturation_point = get_settings().form_window_long * 3  # 30 matches by default
    return min(1.0, matches_played_min / saturation_point)


def _agreement_score(model_probabilities: list[float]) -> float:
    if len(model_probabilities) < 2:
        return 0.5
    spread = statistics.pstdev(model_probabilities)
    return max(0.0, 1.0 - spread / 0.25)


def _calibration_score(calibration_error: float | None) -> float | None:
    if calibration_error is None:
        return None
    return max(0.0, 1.0 - calibration_error / 0.15)


def compute_confidence(inputs: ConfidenceInputs) -> Confidence:
    if inputs.matches_played_min < get_settings().min_matches_for_prediction:
        return Confidence.INSUFFICIENT_DATA

    gap_score = _probability_gap_score(inputs.probabilities)
    volume_score = _data_volume_score(inputs.matches_played_min)
    agreement_score = _agreement_score(inputs.model_home_win_probabilities)
    calibration_score = _calibration_score(inputs.calibration_error)

    if calibration_score is None:
        weights = {"gap": 0.40, "volume": 0.35, "agreement": 0.25}
        composite = (
            weights["gap"] * gap_score
            + weights["volume"] * volume_score
            + weights["agreement"] * agreement_score
        )
    else:
        weights = {"gap": 0.35, "volume": 0.30, "agreement": 0.20, "calibration": 0.15}
        composite = (
            weights["gap"] * gap_score
            + weights["volume"] * volume_score
            + weights["agreement"] * agreement_score
            + weights["calibration"] * calibration_score
        )

    for threshold, level in _THRESHOLDS:
        if composite < threshold:
            return level
    return Confidence.VERY_HIGH
