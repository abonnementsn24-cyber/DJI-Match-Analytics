import math

from app.poisson_model import expected_goals, predict_match, score_matrix


def test_score_matrix_sums_to_one():
    matrix = score_matrix(1.4, 1.1)
    total = sum(sum(row) for row in matrix)
    assert math.isclose(total, 1.0, abs_tol=1e-9)


def test_equal_ratings_favor_home_side():
    lam_home, lam_away = expected_goals(1500, 1500)
    assert lam_home > lam_away  # home advantage still applies


def test_stronger_team_has_higher_win_probability():
    strong_at_home = predict_match(1700, 1400)
    assert strong_at_home.home_win > strong_at_home.away_win
    assert strong_at_home.home_win > 0.5


def test_probabilities_sum_to_one():
    result = predict_match(1550, 1480)
    total = result.home_win + result.draw + result.away_win
    assert math.isclose(total, 1.0, abs_tol=1e-6)


def test_top_scores_are_sorted_descending():
    result = predict_match(1500, 1500)
    probs = [p for _, p in result.top_scores]
    assert probs == sorted(probs, reverse=True)
    assert len(result.top_scores) == 3
