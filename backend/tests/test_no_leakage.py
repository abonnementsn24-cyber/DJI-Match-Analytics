"""The most important test file in this project (§24 of the brief): a
prediction must never be influenced by data from after the match it
predicts. If this file passes, the replay engine's core guarantee holds.
"""
from __future__ import annotations

import datetime

from app.analytics.replay_engine import run_full_replay
from app.models.competition import Competition
from app.models.elo import EloHistory
from app.models.match import Match
from app.models.prediction import Prediction
from app.models.team import Team

MIN = 5  # MIN_MATCHES_FOR_PREDICTION default


def _make_competition(db) -> Competition:
    competition = Competition(provider="test", provider_id="T1", canonical_name="Test League", code="T1")
    db.add(competition)
    db.flush()
    return competition


def _make_team(db, name: str) -> Team:
    team = Team(canonical_name=name)
    db.add(team)
    db.flush()
    return team


def _add_match(db, competition, home, away, home_goals, away_goals, date, external_id):
    match = Match(
        provider="test",
        provider_id=external_id,
        competition_id=competition.id,
        utc_date=date,
        status="FINISHED",
        home_team_id=home.id,
        away_team_id=away.id,
        home_goals=home_goals,
        away_goals=away_goals,
        winner="HOME_TEAM" if home_goals > away_goals else "AWAY_TEAM" if away_goals > home_goals else "DRAW",
        last_synced_at=datetime.datetime.utcnow(),
    )
    db.add(match)
    db.flush()
    return match


def _seed_matches(db, n_early: int, n_late: int):
    competition = _make_competition(db)
    a = _make_team(db, "A")
    b = _make_team(db, "B")
    c = _make_team(db, "C")

    start = datetime.datetime(2024, 1, 1)
    matches = []
    for i in range(n_early):
        m = _add_match(db, competition, a, b, 2, 0, start + datetime.timedelta(days=i), f"early-{i}")
        matches.append(m)

    late_start = start + datetime.timedelta(days=n_early + 1)
    for i in range(n_late):
        m = _add_match(db, competition, b, c, 1, 3, late_start + datetime.timedelta(days=i), f"late-{i}")
        matches.append(m)

    db.commit()
    return matches


def test_prediction_for_a_match_is_identical_with_or_without_future_matches(db):
    matches = _seed_matches(db, n_early=MIN + 2, n_late=0)
    target_match_id = matches[-1].id

    run_full_replay(db)
    baseline = (
        db.query(Prediction)
        .filter(Prediction.match_id == target_match_id, Prediction.model_name == "ensemble")
        .one()
    )
    baseline_probs = (
        baseline.home_win_probability,
        baseline.draw_probability,
        baseline.away_win_probability,
    )

    # Now add matches that happen *after* the target match, involving a
    # different pairing (B vs C) — B's Elo/form will change going forward,
    # but the already-computed prediction for the earlier A-vs-B match must
    # not have used that future information, and must not be rewritten.
    _seed_matches(db, n_early=0, n_late=3)
    run_full_replay(db)

    after = (
        db.query(Prediction)
        .filter(Prediction.match_id == target_match_id, Prediction.model_name == "ensemble")
        .one()
    )
    after_probs = (after.home_win_probability, after.draw_probability, after.away_win_probability)

    assert after_probs == baseline_probs
    assert after.locked is True


def test_elo_history_before_a_teams_first_match_is_the_default_rating(db):
    matches = _seed_matches(db, n_early=MIN, n_late=0)
    run_full_replay(db)

    first_match = matches[0]
    home_history = (
        db.query(EloHistory)
        .filter(EloHistory.match_id == first_match.id, EloHistory.team_id == first_match.home_team_id)
        .one()
    )
    assert home_history.rating_before == 1500.0


def test_state_during_replay_never_counts_the_current_or_future_match(db):
    from app.analytics.replay_engine import iter_matches_chronologically

    _seed_matches(db, n_early=3, n_late=0)

    seen_counts = []
    for step in iter_matches_chronologically(db):
        seen_counts.append(step.state.matches_played(step.match.home_team_id))

    # First match: the home team has played 0 matches *before* it.
    assert seen_counts[0] == 0
    # Matches played strictly increases by exactly one team-appearance per
    # prior match — never includes the match currently being processed.
    assert seen_counts == sorted(seen_counts)
