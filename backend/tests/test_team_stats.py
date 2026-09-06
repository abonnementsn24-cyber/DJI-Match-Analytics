from app.team_stats import TeamStats


def test_record_match_updates_home_and_away_splits():
    stats = TeamStats()
    stats.record_match("Home", "Away", home_goals=2, away_goals=1)

    home = stats.get("Home")
    away = stats.get("Away")

    assert home.home_matches == 1
    assert home.home_goals_for == 2
    assert home.home_goals_against == 1
    assert away.away_matches == 1
    assert away.away_goals_for == 1
    assert away.away_goals_against == 2


def test_recent_form_tracks_results_and_points():
    stats = TeamStats()
    stats.record_match("Home", "Away", home_goals=2, away_goals=0)  # Home wins
    stats.record_match("Away", "Home", home_goals=1, away_goals=1)  # draw

    home = stats.get("Home")
    assert home.matches_played == 2
    form = home.as_dict()["recent_form"]
    assert form["results"] == ["N", "V"]  # most recent first


def test_head_to_head_records_both_orientations():
    stats = TeamStats()
    stats.record_match("A", "B", home_goals=1, away_goals=0)
    stats.record_match("B", "A", home_goals=2, away_goals=2)

    meetings = stats.head_to_head("A", "B")
    assert len(meetings) == 2
    assert stats.head_to_head("B", "A") == meetings


def test_league_averages_default_before_any_match():
    stats = TeamStats()
    assert stats.league_avg_home_goals() > 0
    assert stats.league_avg_away_goals() > 0
