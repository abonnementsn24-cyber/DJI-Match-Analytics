"""After a match finishes, compares each stored prediction to the real
result. Only the evaluation columns are ever written here
(``actual_result``, ``correct``, ``brier_score``, ``log_loss``) — the
original probabilities, ``generated_at`` and ``model_version`` are never
touched, so a prediction's history stays exactly what was said before
kickoff (§15 of the brief).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..analytics.metrics import brier_score, log_loss_single
from ..models.enums import MatchStatus, MatchWinner, Outcome
from ..models.match import Match
from ..models.prediction import Prediction

_WINNER_TO_OUTCOME = {
    MatchWinner.HOME_TEAM: Outcome.HOME,
    MatchWinner.AWAY_TEAM: Outcome.AWAY,
    MatchWinner.DRAW: Outcome.DRAW,
}


def _outcome_from_match(match: Match) -> Outcome | None:
    if match.winner is not None:
        return _WINNER_TO_OUTCOME.get(match.winner)
    if match.home_goals is None or match.away_goals is None:
        return None
    if match.home_goals > match.away_goals:
        return Outcome.HOME
    if match.home_goals < match.away_goals:
        return Outcome.AWAY
    return Outcome.DRAW


def evaluate_finished_predictions(db: Session) -> int:
    pending = (
        db.query(Prediction, Match)
        .join(Match, Prediction.match_id == Match.id)
        .filter(Match.status == MatchStatus.FINISHED, Prediction.actual_result.is_(None))
        .all()
    )

    updated = 0
    for prediction, match in pending:
        outcome = _outcome_from_match(match)
        if outcome is None:
            continue

        predicted = (
            prediction.home_win_probability,
            prediction.draw_probability,
            prediction.away_win_probability,
        )
        prediction.actual_result = outcome
        prediction.correct = prediction.predicted_result == outcome
        prediction.brier_score = brier_score(predicted, outcome.value)
        prediction.log_loss = log_loss_single(predicted, outcome.value)
        updated += 1

    db.commit()
    return updated
