from app.elo import INITIAL_RATING, EloRatings


def test_new_team_starts_at_initial_rating():
    ratings = EloRatings()
    assert ratings.get("Dakar FC") == INITIAL_RATING
    assert ratings.played("Dakar FC") == 0


def test_winner_gains_rating_and_loser_loses_it():
    ratings = EloRatings()
    ratings.record_match("Home", "Away", home_goals=2, away_goals=0)

    assert ratings.get("Home") > INITIAL_RATING
    assert ratings.get("Away") < INITIAL_RATING
    assert ratings.played("Home") == 1
    assert ratings.played("Away") == 1


def test_draw_with_equal_ratings_is_neutral():
    ratings = EloRatings()
    ratings.record_match("Home", "Away", home_goals=1, away_goals=1)

    # Home still gets the home-advantage bonus factored into "expected",
    # so a draw actually costs the home side a little rating.
    assert ratings.get("Home") < INITIAL_RATING
    assert ratings.get("Away") > INITIAL_RATING


def test_bigger_win_moves_rating_more():
    small_win = EloRatings()
    small_win.record_match("Home", "Away", home_goals=1, away_goals=0)

    big_win = EloRatings()
    big_win.record_match("Home", "Away", home_goals=4, away_goals=0)

    small_delta = small_win.get("Home") - INITIAL_RATING
    big_delta = big_win.get("Home") - INITIAL_RATING
    assert big_delta > small_delta
