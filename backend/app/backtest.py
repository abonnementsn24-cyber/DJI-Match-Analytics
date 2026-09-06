"""Backtests the prediction engine over historical matches.

For every stored match (in chronological order), we generate a prediction
from the Elo ratings *as they stood before that match*, then update the
ratings with the real result. This mirrors how the model would have
behaved live, avoiding lookahead bias.

Reports calibration via the multi-class Brier score (lower is better, 0 is
perfect) and simple accuracy of the most-likely outcome.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .elo import EloRatings
from .models import Match
from .predictor import MIN_MATCHES_FOR_PREDICTION
from .poisson_model import predict_match


@dataclass
class BacktestReport:
    matches_evaluated: int
    matches_skipped_insufficient_data: int
    brier_score: float | None
    accuracy: float | None

    def as_dict(self) -> dict:
        return {
            "matches_evaluated": self.matches_evaluated,
            "matches_skipped_insufficient_data": self.matches_skipped_insufficient_data,
            "brier_score": round(self.brier_score, 4) if self.brier_score is not None else None,
            "accuracy": round(self.accuracy, 4) if self.accuracy is not None else None,
        }


def _actual_outcome_vector(home_goals: int, away_goals: int) -> tuple[float, float, float]:
    if home_goals > away_goals:
        return (1.0, 0.0, 0.0)
    if home_goals < away_goals:
        return (0.0, 0.0, 1.0)
    return (0.0, 1.0, 0.0)


def run_backtest(db: Session) -> BacktestReport:
    ratings = EloRatings()
    matches = db.query(Match).order_by(Match.played_at.asc()).all()

    evaluated = 0
    skipped = 0
    brier_total = 0.0
    correct = 0

    for match in matches:
        home_name, away_name = match.home_team.name, match.away_team.name
        home_played, away_played = ratings.played(home_name), ratings.played(away_name)

        if home_played < MIN_MATCHES_FOR_PREDICTION or away_played < MIN_MATCHES_FOR_PREDICTION:
            skipped += 1
        else:
            probabilities = predict_match(ratings.get(home_name), ratings.get(away_name))
            predicted = (probabilities.home_win, probabilities.draw, probabilities.away_win)
            actual = _actual_outcome_vector(match.home_goals, match.away_goals)

            brier_total += sum((p - a) ** 2 for p, a in zip(predicted, actual))
            predicted_outcome = max(range(3), key=lambda i: predicted[i])
            actual_outcome = max(range(3), key=lambda i: actual[i])
            if predicted_outcome == actual_outcome:
                correct += 1
            evaluated += 1

        ratings.record_match(home_name, away_name, match.home_goals, match.away_goals)

    return BacktestReport(
        matches_evaluated=evaluated,
        matches_skipped_insufficient_data=skipped,
        brier_score=(brier_total / evaluated) if evaluated else None,
        accuracy=(correct / evaluated) if evaluated else None,
    )
