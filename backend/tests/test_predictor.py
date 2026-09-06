from app.elo import EloRatings
from app.predictor import MIN_MATCHES_FOR_PREDICTION, predict


def _play_matches(ratings: EloRatings, team: str, opponent: str, count: int) -> None:
    for _ in range(count):
        ratings.record_match(team, opponent, home_goals=1, away_goals=1)


def test_insufficient_data_returns_unreliable_result():
    ratings = EloRatings()
    _play_matches(ratings, "Home", "Away", MIN_MATCHES_FOR_PREDICTION - 1)

    result = predict(ratings, "Home", "Away")

    assert result.reliable is False
    assert result.reason is not None
    assert result.probabilities is None


def test_enough_data_returns_reliable_prediction():
    ratings = EloRatings()
    _play_matches(ratings, "Home", "Away", MIN_MATCHES_FOR_PREDICTION)

    result = predict(ratings, "Home", "Away")

    assert result.reliable is True
    assert result.confidence in {"faible", "moyenne", "elevee"}
    assert result.probabilities is not None

    payload = result.as_dict()
    assert "home_win" in payload
    assert "top_scores" in payload
