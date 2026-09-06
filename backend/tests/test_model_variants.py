import datetime

import pytest

from app.analytics.elo import EloState
from app.analytics.model_variants import (
    MODEL_NAMES,
    MatchContext,
    expected_goals_for_model,
)
from app.analytics.team_state import LeagueState


def _seed(stronger: int, weaker: int, rounds: int = 12) -> tuple[LeagueState, EloState]:
    state, elo = LeagueState(), EloState()
    date = datetime.datetime(2024, 1, 1)
    for i in range(rounds):
        state.record_match(stronger, weaker, home_goals=2, away_goals=0, date=date + datetime.timedelta(days=2 * i))
        elo.record_match(stronger, weaker, home_goals=2, away_goals=0)
        state.record_match(weaker, stronger, home_goals=0, away_goals=2, date=date + datetime.timedelta(days=2 * i + 1))
        elo.record_match(weaker, stronger, home_goals=0, away_goals=2)
    return state, elo


@pytest.mark.parametrize("model", MODEL_NAMES)
def test_stronger_team_gets_higher_expected_goals_at_home(model):
    state, elo = _seed(1, 2)
    ctx = MatchContext(home_team_id=1, away_team_id=2)
    lam_home, lam_away = expected_goals_for_model(model, state, elo, ctx, as_of=datetime.datetime(2024, 6, 1))
    assert lam_home > lam_away


def test_unknown_model_raises():
    state, elo = _seed(1, 2)
    ctx = MatchContext(home_team_id=1, away_team_id=2)
    with pytest.raises(ValueError):
        expected_goals_for_model("not-a-model", state, elo, ctx)


def test_expected_goals_are_clamped_to_sane_range():
    state, elo = LeagueState(), EloState()
    ctx = MatchContext(home_team_id=1, away_team_id=2)
    lam_home, lam_away = expected_goals_for_model("basic", state, elo, ctx)
    assert 0.05 <= lam_home <= 6.0
    assert 0.05 <= lam_away <= 6.0
