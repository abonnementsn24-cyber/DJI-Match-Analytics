"""Three comparable prediction models, from simplest to most complete:

- ``simple``   — attack/defense strength vs. league average, from each
                 team's full home/away history. No Elo, no recent form.
- ``form``     — same idea, but using only each team's last
                 ``FORM_WINDOW`` matches (regardless of venue), so it
                 reacts faster to a team's current run.
- ``combined`` — blends the Elo-based expected goals (elo.py /
                 poisson_model.py) with the recent-form expected goals,
                 then nudges the result by historical head-to-head
                 dominance between the two sides.

Comparing the three (see backtest.py) is how we tell whether the extra
complexity of ``combined`` is actually earning its keep, rather than just
trusting it because it sounds more sophisticated.
"""
from __future__ import annotations

from .elo import EloRatings
from .poisson_model import MatchProbabilities, expected_goals as elo_expected_goals
from .poisson_model import predict_from_matrix, score_matrix
from .team_stats import TeamStats

MODEL_NAMES = ("simple", "form", "combined")
MIN_EXPECTED_GOALS = 0.05
MAX_EXPECTED_GOALS = 6.0
MAX_H2H_ADJUSTMENT = 0.15


def _clamp(lam: float) -> float:
    return max(MIN_EXPECTED_GOALS, min(MAX_EXPECTED_GOALS, lam))


def expected_goals_simple(stats: TeamStats, home: str, away: str) -> tuple[float, float]:
    home_record = stats.get(home)
    away_record = stats.get(away)
    league_avg_home = stats.league_avg_home_goals()
    league_avg_away = stats.league_avg_away_goals()

    home_attack = (
        (home_record.home_goals_for / home_record.home_matches) / league_avg_home
        if home_record and home_record.home_matches
        else 1.0
    )
    away_defense = (
        (away_record.away_goals_against / away_record.away_matches) / league_avg_home
        if away_record and away_record.away_matches
        else 1.0
    )
    away_attack = (
        (away_record.away_goals_for / away_record.away_matches) / league_avg_away
        if away_record and away_record.away_matches
        else 1.0
    )
    home_defense = (
        (home_record.home_goals_against / home_record.home_matches) / league_avg_away
        if home_record and home_record.home_matches
        else 1.0
    )

    return league_avg_home * home_attack * away_defense, league_avg_away * away_attack * home_defense


def expected_goals_form(stats: TeamStats, home: str, away: str) -> tuple[float, float]:
    league_avg = stats.league_avg_goals_per_match()
    league_avg_home = stats.league_avg_home_goals()
    league_avg_away = stats.league_avg_away_goals()

    home_record = stats.get(home)
    away_record = stats.get(away)

    def recent_attack(record) -> float:
        if not record or not record.recent:
            return 1.0
        avg = sum(g for g, _, _ in record.recent) / len(record.recent)
        return avg / league_avg if league_avg else 1.0

    def recent_defense(record) -> float:
        if not record or not record.recent:
            return 1.0
        avg = sum(g for _, g, _ in record.recent) / len(record.recent)
        return avg / league_avg if league_avg else 1.0

    lam_home = league_avg_home * recent_attack(home_record) * recent_defense(away_record)
    lam_away = league_avg_away * recent_attack(away_record) * recent_defense(home_record)
    return lam_home, lam_away


def _h2h_adjustment(stats: TeamStats, home: str, away: str) -> tuple[float, float]:
    """Small multiplicative nudge based on historical goal difference between
    the two sides (from ``home``'s perspective), capped at ±15%."""
    meetings = stats.head_to_head(home, away)
    if not meetings:
        return 1.0, 1.0

    total_diff = 0
    for played_home, played_away, home_goals, away_goals in meetings:
        if played_home == home:
            total_diff += home_goals - away_goals
        else:
            total_diff += away_goals - home_goals

    avg_diff = total_diff / len(meetings)
    adjustment = max(-MAX_H2H_ADJUSTMENT, min(MAX_H2H_ADJUSTMENT, avg_diff * 0.05))
    return 1 + adjustment, 1 - adjustment


def expected_goals_combined(
    ratings: EloRatings, stats: TeamStats, home: str, away: str
) -> tuple[float, float]:
    lam_home_elo, lam_away_elo = elo_expected_goals(ratings.get(home), ratings.get(away))
    lam_home_form, lam_away_form = expected_goals_form(stats, home, away)

    lam_home = (lam_home_elo + lam_home_form) / 2
    lam_away = (lam_away_elo + lam_away_form) / 2

    factor_home, factor_away = _h2h_adjustment(stats, home, away)
    return lam_home * factor_home, lam_away * factor_away


def expected_goals_for_model(
    model: str, ratings: EloRatings, stats: TeamStats, home: str, away: str
) -> tuple[float, float]:
    if model == "simple":
        lam_home, lam_away = expected_goals_simple(stats, home, away)
    elif model == "form":
        lam_home, lam_away = expected_goals_form(stats, home, away)
    elif model == "combined":
        lam_home, lam_away = expected_goals_combined(ratings, stats, home, away)
    else:
        raise ValueError(f"Modèle inconnu: {model!r} (attendu: {MODEL_NAMES})")
    return _clamp(lam_home), _clamp(lam_away)


def predict_with_model(
    model: str, ratings: EloRatings, stats: TeamStats, home: str, away: str
) -> MatchProbabilities:
    lam_home, lam_away = expected_goals_for_model(model, ratings, stats, home, away)
    matrix = score_matrix(lam_home, lam_away)
    return predict_from_matrix(matrix, lam_home, lam_away)
