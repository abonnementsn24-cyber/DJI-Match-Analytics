import pytest

from app.elo import EloRatings
from app.predictor import MIN_MATCHES_FOR_PREDICTION, predict
from app.team_stats import TeamStats
from app.variants import MODEL_NAMES


def _play_matches(ratings: EloRatings, stats: TeamStats, team: str, opponent: str, count: int) -> None:
    for _ in range(count):
        ratings.record_match(team, opponent, home_goals=1, away_goals=1)
        stats.record_match(team, opponent, home_goals=1, away_goals=1)


def test_insufficient_data_returns_unreliable_result():
    ratings, stats = EloRatings(), TeamStats()
    _play_matches(ratings, stats, "Home", "Away", MIN_MATCHES_FOR_PREDICTION - 1)

    result = predict(ratings, stats, "Home", "Away")

    assert result.reliable is False
    assert result.reason is not None
    assert result.probabilities is None


def test_enough_data_returns_reliable_prediction():
    ratings, stats = EloRatings(), TeamStats()
    _play_matches(ratings, stats, "Home", "Away", MIN_MATCHES_FOR_PREDICTION)

    result = predict(ratings, stats, "Home", "Away")

    assert result.reliable is True
    assert result.confidence in {"faible", "moyenne", "elevee"}
    assert result.probabilities is not None

    payload = result.as_dict()
    assert "home_win" in payload
    assert "top_scores" in payload
    assert payload["model"] == "combined"


@pytest.mark.parametrize("model", MODEL_NAMES)
def test_every_model_produces_a_valid_prediction(model):
    ratings, stats = EloRatings(), TeamStats()
    _play_matches(ratings, stats, "Home", "Away", MIN_MATCHES_FOR_PREDICTION)

    result = predict(ratings, stats, "Home", "Away", model=model)

    assert result.reliable is True
    total = result.probabilities.home_win + result.probabilities.draw + result.probabilities.away_win
    assert total == pytest.approx(1.0, abs=1e-6)


def test_unknown_model_raises():
    ratings, stats = EloRatings(), TeamStats()
    _play_matches(ratings, stats, "Home", "Away", MIN_MATCHES_FOR_PREDICTION)

    with pytest.raises(ValueError):
        predict(ratings, stats, "Home", "Away", model="not-a-model")
