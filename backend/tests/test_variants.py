import pytest

from app.elo import EloRatings
from app.team_stats import TeamStats
from app.variants import (
    MODEL_NAMES,
    expected_goals_combined,
    expected_goals_form,
    expected_goals_simple,
    predict_with_model,
)


def _seed(stronger: str, weaker: str, rounds: int = 12) -> tuple[EloRatings, TeamStats]:
    ratings, stats = EloRatings(), TeamStats()
    for _ in range(rounds):
        ratings.record_match(stronger, weaker, home_goals=2, away_goals=0)
        stats.record_match(stronger, weaker, home_goals=2, away_goals=0)
        ratings.record_match(weaker, stronger, home_goals=0, away_goals=2)
        stats.record_match(weaker, stronger, home_goals=0, away_goals=2)
    return ratings, stats


def test_simple_model_favors_team_with_better_scoring_record():
    _, stats = _seed("Strong", "Weak")
    lam_home, lam_away = expected_goals_simple(stats, "Strong", "Weak")
    assert lam_home > lam_away


def test_form_model_favors_team_with_better_recent_record():
    _, stats = _seed("Strong", "Weak")
    lam_home, lam_away = expected_goals_form(stats, "Strong", "Weak")
    assert lam_home > lam_away


def test_combined_model_favors_stronger_team_and_uses_h2h():
    ratings, stats = _seed("Strong", "Weak")
    lam_home, lam_away = expected_goals_combined(ratings, stats, "Strong", "Weak")
    assert lam_home > lam_away


def test_team_with_no_history_defaults_to_league_average():
    stats = TeamStats()
    lam_home, lam_away = expected_goals_simple(stats, "Nobody", "Nowhere")
    assert lam_home == pytest.approx(stats.league_avg_home_goals())
    assert lam_away == pytest.approx(stats.league_avg_away_goals())


@pytest.mark.parametrize("model", MODEL_NAMES)
def test_predict_with_model_returns_normalized_probabilities(model):
    ratings, stats = _seed("Strong", "Weak")
    result = predict_with_model(model, ratings, stats, "Strong", "Weak")
    total = result.home_win + result.draw + result.away_win
    assert total == pytest.approx(1.0, abs=1e-6)


def test_unknown_model_raises():
    ratings, stats = _seed("Strong", "Weak")
    with pytest.raises(ValueError):
        predict_with_model("nope", ratings, stats, "Strong", "Weak")
