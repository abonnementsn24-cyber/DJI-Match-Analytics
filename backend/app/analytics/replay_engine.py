"""Walks every stored match in chronological order exactly once, building
up global Elo + team-state as it goes, and is the *only* place allowed to
decide what a model "knew" before a given match. Both prediction
generation and ML training consume this walk so they can never see a
different (leakier) view of history than each other.

Contract for consumers of ``iter_matches_chronologically``: everything you
need from ``step.state``/``step.elo`` must be read *before* your loop body
returns control to the generator (i.e. before ``next()`` is called again).
The generator mutates its internal state for the *next* item only after
resuming — plain synchronous ``for step in iter_matches_chronologically(db):
...`` bodies satisfy this automatically; do not stash a ``ReplayStep`` in a
list to process later.
"""
from __future__ import annotations

import datetime
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.logging import get_logger
from ..models.elo import EloHistory
from ..models.enums import Confidence, Outcome
from ..models.match import Match
from ..models.prediction import Prediction
from .confidence import ConfidenceInputs, compute_confidence
from .elo import EloState, EloUpdate
from .model_variants import MODEL_NAMES, MatchContext, expected_goals_for_model
from .poisson import predict_match
from .team_state import LeagueState

logger = get_logger(__name__)

MODEL_VERSION = "1.0.0"


@dataclass
class ReplayStep:
    match: Match
    state: LeagueState
    elo: EloState
    ctx: MatchContext
    # Pre-computed (pure, not-yet-applied) Elo update for this match, so
    # consumers can persist a before/after snapshot without recomputing the
    # formula themselves. None for matches with no result yet.
    elo_update: EloUpdate | None


def iter_matches_chronologically(db: Session) -> Iterator[ReplayStep]:
    state = LeagueState()
    elo = EloState()

    matches = db.query(Match).order_by(Match.utc_date.asc(), Match.id.asc()).all()
    for match in matches:
        ctx = MatchContext(home_team_id=match.home_team_id, away_team_id=match.away_team_id)
        elo_update = (
            elo.compute_update(match.home_team_id, match.away_team_id, match.home_goals, match.away_goals)
            if match.is_finished
            else None
        )
        yield ReplayStep(match=match, state=state, elo=elo, ctx=ctx, elo_update=elo_update)

        if match.is_finished:
            state.record_match(
                match.home_team_id,
                match.away_team_id,
                match.home_goals,
                match.away_goals,
                match.utc_date,
            )
            elo.apply_update(match.home_team_id, match.away_team_id, elo_update)


def _outcome_from_probabilities(home: float, draw: float, away: float) -> Outcome:
    best = max(home, draw, away)
    if best == home:
        return Outcome.HOME
    if best == draw:
        return Outcome.DRAW
    return Outcome.AWAY


def build_current_state(db: Session) -> tuple[LeagueState, EloState]:
    """Fully drains the chronological replay and returns the resulting
    state — i.e. Elo ratings and form *as of right now*, for display
    purposes (team pages, "current form"). This is not used for historical
    predictions, which must only ever see state as of before their own
    match; see ``iter_matches_chronologically``.
    """
    state = LeagueState()
    elo = EloState()
    for step in iter_matches_chronologically(db):
        state = step.state
        elo = step.elo
    return state, elo


def run_full_replay(
    db: Session,
    models: tuple[str, ...] = MODEL_NAMES,
    ml_predict_fn: Callable[[LeagueState, EloState, MatchContext, datetime.datetime], tuple | None]
    | None = None,
    competition_ids: set[int] | None = None,
) -> dict:
    """Single global chronological pass: persists Elo history for every
    finished match, and a prediction per requested model for every match
    where both teams already have enough history. Idempotent — re-running
    it only fills in gaps (new matches, or an ``ml`` model that just became
    available) and never rewrites a locked prediction's probabilities.
    """
    settings = get_settings()
    now = datetime.datetime.utcnow()

    predictions_created = 0
    predictions_refreshed = 0
    predictions_skipped_insufficient_data = 0
    elo_rows_created = 0

    for step in iter_matches_chronologically(db):
        match = step.match
        home_played = step.state.matches_played(match.home_team_id)
        away_played = step.state.matches_played(match.away_team_id)
        enough_data = (
            home_played >= settings.min_matches_for_prediction
            and away_played >= settings.min_matches_for_prediction
        )

        wanted = competition_ids is None or match.competition_id in competition_ids

        if enough_data and wanted:
            model_home_probs: dict[str, float] = {}
            model_results: dict[str, tuple] = {}

            for model_name in models:
                if model_name == "ml":
                    if ml_predict_fn is None:
                        continue
                    result = ml_predict_fn(step.state, step.elo, step.ctx, match.utc_date)
                    if result is None:
                        continue
                    home_p, draw_p, away_p, exp_home, exp_away = result
                else:
                    lam_home, lam_away = expected_goals_for_model(
                        model_name, step.state, step.elo, step.ctx, as_of=match.utc_date
                    )
                    probs = predict_match(lam_home, lam_away)
                    home_p, draw_p, away_p = probs.home_win, probs.draw, probs.away_win
                    exp_home, exp_away = probs.expected_home_goals, probs.expected_away_goals

                model_home_probs[model_name] = home_p
                model_results[model_name] = (home_p, draw_p, away_p, exp_home, exp_away)

            for model_name, (home_p, draw_p, away_p, exp_home, exp_away) in model_results.items():
                confidence = compute_confidence(
                    ConfidenceInputs(
                        probabilities=(home_p, draw_p, away_p),
                        matches_played_min=min(home_played, away_played),
                        model_home_win_probabilities=list(model_home_probs.values()),
                    )
                )
                created, refreshed = _upsert_prediction(
                    db,
                    match=match,
                    model_name=model_name,
                    home_p=home_p,
                    draw_p=draw_p,
                    away_p=away_p,
                    exp_home=exp_home,
                    exp_away=exp_away,
                    confidence=confidence,
                    now=now,
                )
                predictions_created += created
                predictions_refreshed += refreshed
        elif wanted:
            predictions_skipped_insufficient_data += 1

        if match.is_finished:
            elo_rows_created += _persist_elo_history_for_match(db, match, step.elo_update)

    db.commit()
    return {
        "predictions_created": predictions_created,
        "predictions_refreshed": predictions_refreshed,
        "predictions_skipped_insufficient_data": predictions_skipped_insufficient_data,
        "elo_rows_created": elo_rows_created,
    }


def _persist_elo_history_for_match(db: Session, match: Match, elo_update: EloUpdate) -> int:
    exists = db.query(EloHistory.id).filter(EloHistory.match_id == match.id).first()
    if exists:
        return 0

    db.add(
        EloHistory(
            team_id=match.home_team_id,
            match_id=match.id,
            rating_before=elo_update.home_before,
            rating_after=elo_update.home_after,
            date=match.utc_date,
        )
    )
    db.add(
        EloHistory(
            team_id=match.away_team_id,
            match_id=match.id,
            rating_before=elo_update.away_before,
            rating_after=elo_update.away_after,
            date=match.utc_date,
        )
    )
    return 2


def _upsert_prediction(
    db: Session,
    match: Match,
    model_name: str,
    home_p: float,
    draw_p: float,
    away_p: float,
    exp_home: float,
    exp_away: float,
    confidence: Confidence,
    now: datetime.datetime,
) -> tuple[int, int]:
    existing = (
        db.query(Prediction)
        .filter(
            Prediction.match_id == match.id,
            Prediction.model_name == model_name,
            Prediction.model_version == MODEL_VERSION,
        )
        .one_or_none()
    )

    should_lock = match.utc_date <= now

    if existing is not None:
        if existing.locked:
            return 0, 0
        existing.home_win_probability = home_p
        existing.draw_probability = draw_p
        existing.away_win_probability = away_p
        existing.expected_home_goals = exp_home
        existing.expected_away_goals = exp_away
        existing.confidence = confidence
        existing.predicted_result = _outcome_from_probabilities(home_p, draw_p, away_p)
        existing.generated_at = now
        existing.locked = should_lock
        return 0, 1

    db.add(
        Prediction(
            match_id=match.id,
            model_name=model_name,
            model_version=MODEL_VERSION,
            generated_at=now,
            locked=should_lock,
            home_win_probability=home_p,
            draw_probability=draw_p,
            away_win_probability=away_p,
            expected_home_goals=exp_home,
            expected_away_goals=exp_away,
            confidence=confidence,
            predicted_result=_outcome_from_probabilities(home_p, draw_p, away_p),
        )
    )
    return 1, 0
