"""Numeric feature vector for the ML model — built from exactly the same
pre-match state (``LeagueState`` + ``EloState``) the other four model
variants read from, so it carries no more information than they have.
"""
from __future__ import annotations

import datetime

from ..analytics.elo import EloState
from ..analytics.model_variants import MatchContext
from ..analytics.team_state import LeagueState

FEATURE_NAMES = [
    "elo_diff",
    "home_attack_basic",
    "away_defense_basic",
    "away_attack_basic",
    "home_defense_basic",
    "home_form_ppm",
    "away_form_ppm",
    "home_form_goals_for_avg",
    "away_form_goals_for_avg",
    "h2h_avg_goal_diff",
    "h2h_matches",
    "rest_days_diff",
]


def build_feature_vector(
    state: LeagueState, elo: EloState, ctx: MatchContext, as_of: datetime.datetime
) -> list[float]:
    home = state.get(ctx.home_team_id)
    away = state.get(ctx.away_team_id)
    league_home = state.league_avg_home_goals()
    league_away = state.league_avg_away_goals()

    elo_diff = (elo.get(ctx.home_team_id) + elo.home_advantage) - elo.get(ctx.away_team_id)

    home_attack_basic = (
        (home.home_goals_for / home.home_matches) / league_home if home and home.home_matches else 1.0
    )
    away_defense_basic = (
        (away.away_goals_against / away.away_matches) / league_home if away and away.away_matches else 1.0
    )
    away_attack_basic = (
        (away.away_goals_for / away.away_matches) / league_away if away and away.away_matches else 1.0
    )
    home_defense_basic = (
        (home.home_goals_against / home.home_matches) / league_away if home and home.home_matches else 1.0
    )

    home_form = home.form(10, "home") if home else None
    away_form = away.form(10, "away") if away else None

    meetings = state.head_to_head(ctx.home_team_id, ctx.away_team_id)
    if meetings:
        total_diff = 0
        for home_id, _away_id, hg, ag, _date in meetings:
            total_diff += (hg - ag) if home_id == ctx.home_team_id else (ag - hg)
        h2h_avg_diff = total_diff / len(meetings)
    else:
        h2h_avg_diff = 0.0

    home_rest = state.rest_days_for(ctx.home_team_id, as_of)
    away_rest = state.rest_days_for(ctx.away_team_id, as_of)
    rest_diff = (home_rest - away_rest) if home_rest is not None and away_rest is not None else 0

    return [
        elo_diff,
        home_attack_basic,
        away_defense_basic,
        away_attack_basic,
        home_defense_basic,
        home_form["points_per_match"] if home_form else 1.0,
        away_form["points_per_match"] if away_form else 1.0,
        home_form["avg_goals_for"] if home_form else league_home,
        away_form["avg_goals_for"] if away_form else league_away,
        h2h_avg_diff,
        len(meetings),
        rest_diff,
    ]
