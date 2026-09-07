import math

from app.analytics.poisson import predict_match, score_matrix


def test_score_matrix_sums_to_one():
    matrix = score_matrix(1.4, 1.1)
    total = sum(sum(row) for row in matrix)
    assert math.isclose(total, 1.0, abs_tol=1e-9)


def test_stronger_home_side_has_higher_win_probability():
    result = predict_match(1.8, 0.9)
    assert result.home_win > result.away_win
    assert result.home_win > 0.5


def test_probabilities_sum_to_one():
    result = predict_match(1.5, 1.2)
    total = result.home_win + result.draw + result.away_win
    assert math.isclose(total, 1.0, abs_tol=1e-6)


def test_top_scores_sorted_descending_and_limited():
    result = predict_match(1.4, 1.1, top_n=5)
    probs = [p for _, p in result.top_scores]
    assert probs == sorted(probs, reverse=True)
    assert len(result.top_scores) == 5


def test_as_dict_contains_expected_keys():
    result = predict_match(1.3, 1.0)
    payload = result.as_dict()
    for key in (
        "home_win_probability",
        "draw_probability",
        "away_win_probability",
        "btts_probability",
        "over_2_5_probability",
        "expected_home_goals",
        "expected_away_goals",
        "top_scores",
    ):
        assert key in payload
