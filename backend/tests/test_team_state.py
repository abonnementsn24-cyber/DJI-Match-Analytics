import datetime

from app.analytics.team_state import LeagueState


def test_record_match_updates_home_and_away_splits():
    state = LeagueState()
    state.record_match(1, 2, home_goals=2, away_goals=1, date=datetime.datetime(2024, 1, 1))

    home = state.get(1)
    away = state.get(2)

    assert home.home_matches == 1
    assert home.home_goals_for == 2
    assert home.home_goals_against == 1
    assert away.away_matches == 1
    assert away.away_goals_for == 1
    assert away.away_goals_against == 2


def test_form_window_respects_venue_split():
    state = LeagueState()
    state.record_match(1, 2, home_goals=3, away_goals=0, date=datetime.datetime(2024, 1, 1))
    state.record_match(2, 1, home_goals=0, away_goals=0, date=datetime.datetime(2024, 1, 8))

    team1 = state.get(1)
    home_form = team1.form(10, "home")
    away_form = team1.form(10, "away")

    assert home_form["matches"] == 1
    assert home_form["goals_for"] == 3
    assert away_form["matches"] == 1
    assert away_form["goals_for"] == 0


def test_head_to_head_symmetric_and_limited_to_max_matches():
    state = LeagueState()
    for i in range(7):
        state.record_match(1, 2, home_goals=1, away_goals=0, date=datetime.datetime(2024, 1, 1 + i))

    meetings_a = state.head_to_head(1, 2, max_matches=5)
    meetings_b = state.head_to_head(2, 1, max_matches=5)
    assert len(meetings_a) == 5
    assert meetings_a == meetings_b


def test_rest_days_none_before_first_match():
    state = LeagueState()
    assert state.rest_days_for(1, datetime.datetime(2024, 1, 1)) is None

    state.record_match(1, 2, home_goals=1, away_goals=1, date=datetime.datetime(2024, 1, 1))
    assert state.rest_days_for(1, datetime.datetime(2024, 1, 8)) == 7


def test_league_averages_default_before_any_match():
    state = LeagueState()
    assert state.league_avg_home_goals() > 0
    assert state.league_avg_away_goals() > 0
