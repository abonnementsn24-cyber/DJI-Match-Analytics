"""Four independent, comparable expected-goals models (a fifth, ML-based,
lives in app/ml/ since it needs a trained artifact rather than a pure
function). Every function here takes only state built up to — never past
— the match being predicted.

- ``basic``: attack/defense strength vs. league average, from each team's
  full home/away history.
- ``form``: same idea, but restricted to each team's last N home/away
  matches, so it reacts to a current hot or cold streak.
- ``elo``: expected goals derived purely from the Elo rating gap.
- ``ensemble``: a configurable blend of the three above, nudged by
  head-to-head history and (when known) the rest-days gap between the
  two sides.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..core.config import get_settings
from .elo import EloState
from .team_state import LeagueState

MODEL_NAMES = ("basic", "form", "elo", "ensemble")
MIN_EXPECTED_GOALS = 0.05
MAX_EXPECTED_GOALS = 6.0

ELO_LEAGUE_AVG_HOME_GOALS = 1.45
ELO_LEAGUE_AVG_AWAY_GOALS = 1.15
ELO_RATING_SCALE = 400.0
ELO_GOAL_SENSITIVITY = 0.42


def _clamp(lam: float) -> float:
    return max(MIN_EXPECTED_GOALS, min(MAX_EXPECTED_GOALS, lam))


@dataclass
class MatchContext:
    home_team_id: int
    away_team_id: int


def expected_goals_basic(state: LeagueState, ctx: MatchContext) -> tuple[float, float]:
    home = state.get(ctx.home_team_id)
    away = state.get(ctx.away_team_id)
    league_home = state.league_avg_home_goals()
    league_away = state.league_avg_away_goals()

    home_attack = (home.home_goals_for / home.home_matches) / league_home if home and home.home_matches else 1.0
    away_defense = (away.away_goals_against / away.away_matches) / league_home if away and away.away_matches else 1.0
    away_attack = (away.away_goals_for / away.away_matches) / league_away if away and away.away_matches else 1.0
    home_defense = (home.home_goals_against / home.home_matches) / league_away if home and home.home_matches else 1.0

    return league_home * home_attack * away_defense, league_away * away_attack * home_defense


def expected_goals_form(state: LeagueState, ctx: MatchContext) -> tuple[float, float]:
    settings = get_settings()
    window = settings.form_window_long
    league_home = state.league_avg_home_goals()
    league_away = state.league_avg_away_goals()

    home = state.get(ctx.home_team_id)
    away = state.get(ctx.away_team_id)

    home_form = home.form(window, "home") if home else None
    away_form = away.form(window, "away") if away else None

    home_attack = (home_form["avg_goals_for"] / league_home) if home_form else 1.0
    away_defense = (away_form["avg_goals_against"] / league_home) if away_form else 1.0
    away_attack = (away_form["avg_goals_for"] / league_away) if away_form else 1.0
    home_defense = (home_form["avg_goals_against"] / league_away) if home_form else 1.0

    return league_home * home_attack * away_defense, league_away * away_attack * home_defense


def expected_goals_elo(elo: EloState, ctx: MatchContext) -> tuple[float, float]:
    """Converts the Elo rating gap directly into expected goals, independent
    of any goals-based statistic."""
    diff = (elo.get(ctx.home_team_id) + elo.home_advantage) - elo.get(ctx.away_team_id)
    home_factor = math.exp(ELO_GOAL_SENSITIVITY * diff / ELO_RATING_SCALE)
    away_factor = math.exp(-ELO_GOAL_SENSITIVITY * diff / ELO_RATING_SCALE)
    return ELO_LEAGUE_AVG_HOME_GOALS * home_factor, ELO_LEAGUE_AVG_AWAY_GOALS * away_factor


def _h2h_adjustment(state: LeagueState, ctx: MatchContext) -> tuple[float, float]:
    meetings = state.head_to_head(ctx.home_team_id, ctx.away_team_id)
    if not meetings:
        return 1.0, 1.0

    total_diff = 0
    for home_id, _away_id, hg, ag, _date in meetings:
        if home_id == ctx.home_team_id:
            total_diff += hg - ag
        else:
            total_diff += ag - hg

    avg_diff = total_diff / len(meetings)
    cap = get_settings().ensemble_h2h_max_adjustment
    adjustment = max(-cap, min(cap, avg_diff * 0.05))
    return 1 + adjustment, 1 - adjustment


def _rest_adjustment(state: LeagueState, ctx: MatchContext, as_of) -> tuple[float, float]:
    home_rest = state.rest_days_for(ctx.home_team_id, as_of)
    away_rest = state.rest_days_for(ctx.away_team_id, as_of)
    if home_rest is None or away_rest is None:
        return 1.0, 1.0

    cap = get_settings().ensemble_rest_max_adjustment
    diff_days = max(-14, min(14, home_rest - away_rest))
    adjustment = max(-cap, min(cap, diff_days * (cap / 14)))
    return 1 + adjustment, 1 - adjustment


def expected_goals_ensemble(
    state: LeagueState, elo: EloState, ctx: MatchContext, as_of
) -> tuple[float, float]:
    settings = get_settings()
    basic_h, basic_a = expected_goals_basic(state, ctx)
    form_h, form_a = expected_goals_form(state, ctx)
    elo_h, elo_a = expected_goals_elo(elo, ctx)

    lam_home = (
        settings.ensemble_weight_basic * basic_h
        + settings.ensemble_weight_form * form_h
        + settings.ensemble_weight_elo * elo_h
    )
    lam_away = (
        settings.ensemble_weight_basic * basic_a
        + settings.ensemble_weight_form * form_a
        + settings.ensemble_weight_elo * elo_a
    )

    h2h_home, h2h_away = _h2h_adjustment(state, ctx)
    rest_home, rest_away = _rest_adjustment(state, ctx, as_of)

    return lam_home * h2h_home * rest_home, lam_away * h2h_away * rest_away


def expected_goals_for_model(
    model: str, state: LeagueState, elo: EloState, ctx: MatchContext, as_of=None
) -> tuple[float, float]:
    if model == "basic":
        lam_home, lam_away = expected_goals_basic(state, ctx)
    elif model == "form":
        lam_home, lam_away = expected_goals_form(state, ctx)
    elif model == "elo":
        lam_home, lam_away = expected_goals_elo(elo, ctx)
    elif model == "ensemble":
        lam_home, lam_away = expected_goals_ensemble(state, elo, ctx, as_of)
    else:
        raise ValueError(f"Modèle inconnu: {model!r} (attendu: {MODEL_NAMES})")
    return _clamp(lam_home), _clamp(lam_away)
