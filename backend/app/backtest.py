"""Backtests the prediction models over historical matches.

For every stored match (in chronological order), we generate a prediction
from the state (Elo ratings + team stats) *as it stood before that match*,
then update the state with the real result. This mirrors how a model would
have behaved live, avoiding lookahead bias.

Reports:
- Brier score (multi-class, lower is better, 0 is perfect calibration)
- Log loss (lower is better)
- Accuracy of the most-likely outcome
- A calibration curve: matches bucketed by predicted probability, showing
  whether e.g. "60-70% favourites" really won about 60-70% of the time.

``run_backtest_compare`` runs all three model variants and reports which
one actually has the best (lowest) Brier score on the stored history,
instead of assuming the most complex model is the best one.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from sqlalchemy.orm import Session

from .elo import EloRatings
from .models import Match
from .predictor import MIN_MATCHES_FOR_PREDICTION
from .team_stats import TeamStats
from .variants import MODEL_NAMES, predict_with_model

CALIBRATION_BUCKET_SIZE = 0.1
LOG_LOSS_EPSILON = 1e-6


@dataclass
class BacktestReport:
    model: str
    matches_evaluated: int
    matches_skipped_insufficient_data: int
    brier_score: float | None
    log_loss: float | None
    accuracy: float | None
    calibration_curve: list[dict]

    def as_dict(self) -> dict:
        return {
            "model": self.model,
            "matches_evaluated": self.matches_evaluated,
            "matches_skipped_insufficient_data": self.matches_skipped_insufficient_data,
            "brier_score": round(self.brier_score, 4) if self.brier_score is not None else None,
            "log_loss": round(self.log_loss, 4) if self.log_loss is not None else None,
            "accuracy": round(self.accuracy, 4) if self.accuracy is not None else None,
            "calibration_curve": self.calibration_curve,
        }


def _actual_outcome_vector(home_goals: int, away_goals: int) -> tuple[float, float, float]:
    if home_goals > away_goals:
        return (1.0, 0.0, 0.0)
    if home_goals < away_goals:
        return (0.0, 0.0, 1.0)
    return (0.0, 1.0, 0.0)


def _calibration_curve(samples: list[tuple[float, bool]]) -> list[dict]:
    """``samples`` is a list of (predicted_probability, was_correct) for the
    model's own favourite outcome in each match. Buckets by predicted prob."""
    buckets: dict[int, list[bool]] = {}
    for predicted, correct in samples:
        bucket = min(int(predicted / CALIBRATION_BUCKET_SIZE), int(1 / CALIBRATION_BUCKET_SIZE) - 1)
        buckets.setdefault(bucket, []).append(correct)

    curve = []
    for bucket in sorted(buckets):
        outcomes = buckets[bucket]
        curve.append(
            {
                "predicted_range": f"{bucket * CALIBRATION_BUCKET_SIZE:.0%}-{(bucket + 1) * CALIBRATION_BUCKET_SIZE:.0%}",
                "matches": len(outcomes),
                "actual_frequency": round(sum(outcomes) / len(outcomes), 4),
            }
        )
    return curve


def run_backtest(db: Session, model: str = "combined") -> BacktestReport:
    if model not in MODEL_NAMES:
        raise ValueError(f"Modèle inconnu: {model!r} (attendu: {MODEL_NAMES})")

    ratings = EloRatings()
    stats = TeamStats()
    matches = db.query(Match).order_by(Match.played_at.asc()).all()

    evaluated = 0
    skipped = 0
    brier_total = 0.0
    log_loss_total = 0.0
    correct = 0
    calibration_samples: list[tuple[float, bool]] = []

    for match in matches:
        home_name, away_name = match.home_team.name, match.away_team.name
        home_played = stats.matches_played(home_name)
        away_played = stats.matches_played(away_name)

        if home_played < MIN_MATCHES_FOR_PREDICTION or away_played < MIN_MATCHES_FOR_PREDICTION:
            skipped += 1
        else:
            probabilities = predict_with_model(model, ratings, stats, home_name, away_name)
            predicted = (probabilities.home_win, probabilities.draw, probabilities.away_win)
            actual = _actual_outcome_vector(match.home_goals, match.away_goals)

            brier_total += sum((p - a) ** 2 for p, a in zip(predicted, actual))

            actual_outcome = max(range(3), key=lambda i: actual[i])
            log_loss_total += -math.log(max(predicted[actual_outcome], LOG_LOSS_EPSILON))

            predicted_outcome = max(range(3), key=lambda i: predicted[i])
            is_correct = predicted_outcome == actual_outcome
            if is_correct:
                correct += 1
            calibration_samples.append((predicted[predicted_outcome], is_correct))

            evaluated += 1

        ratings.record_match(home_name, away_name, match.home_goals, match.away_goals)
        stats.record_match(home_name, away_name, match.home_goals, match.away_goals)

    return BacktestReport(
        model=model,
        matches_evaluated=evaluated,
        matches_skipped_insufficient_data=skipped,
        brier_score=(brier_total / evaluated) if evaluated else None,
        log_loss=(log_loss_total / evaluated) if evaluated else None,
        accuracy=(correct / evaluated) if evaluated else None,
        calibration_curve=_calibration_curve(calibration_samples),
    )


def run_backtest_compare(db: Session) -> dict:
    reports = {model: run_backtest(db, model) for model in MODEL_NAMES}
    scored = {model: r.brier_score for model, r in reports.items() if r.brier_score is not None}
    best_model = min(scored, key=scored.get) if scored else None

    return {
        "best_model": best_model,
        "models": {model: report.as_dict() for model, report in reports.items()},
    }
