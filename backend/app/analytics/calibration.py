"""Recalibrates raw model probabilities against observed outcome
frequencies (§8 of the brief): one-vs-rest isotonic regression per outcome
(home/draw/away), falling back to Platt scaling when there isn't enough
history for isotonic regression to be stable, and to the identity mapping
when there's barely any history at all.

This is deliberately separate from ``analytics/metrics.py``'s
``calibration_curve``/``calibration_error``, which only *measure* how
well-calibrated a model is — this module actually *corrects* it.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

OUTCOMES = ("HOME", "DRAW", "AWAY")
MIN_SAMPLES_FOR_ISOTONIC = 200
MIN_SAMPLES_FOR_PLATT = 30


@dataclass
class CalibratorSet:
    method: str  # "isotonic" | "platt" | "identity"
    calibrators: dict[str, object] | None = None

    def apply(self, probabilities: tuple[float, float, float]) -> tuple[float, float, float]:
        if self.method == "identity" or self.calibrators is None:
            return probabilities

        adjusted = []
        for outcome, p in zip(OUTCOMES, probabilities, strict=True):
            model = self.calibrators[outcome]
            if self.method == "isotonic":
                adjusted.append(float(model.predict([p])[0]))
            else:  # platt
                adjusted.append(float(model.predict_proba([[p]])[0][1]))

        total = sum(adjusted) or 1.0
        return tuple(v / total for v in adjusted)


def fit_calibrators(
    predicted_probabilities: list[tuple[float, float, float]], actual_outcomes: list[str]
) -> CalibratorSet:
    n = len(actual_outcomes)
    if n < MIN_SAMPLES_FOR_PLATT:
        return CalibratorSet(method="identity")

    method = "isotonic" if n >= MIN_SAMPLES_FOR_ISOTONIC else "platt"
    calibrators: dict[str, object] = {}

    for index, outcome in enumerate(OUTCOMES):
        x = np.array([p[index] for p in predicted_probabilities])
        y = np.array([1 if actual == outcome else 0 for actual in actual_outcomes])

        if method == "isotonic":
            model = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            model.fit(x, y)
        else:
            model = LogisticRegression()
            model.fit(x.reshape(-1, 1), y)

        calibrators[outcome] = model

    return CalibratorSet(method=method, calibrators=calibrators)
