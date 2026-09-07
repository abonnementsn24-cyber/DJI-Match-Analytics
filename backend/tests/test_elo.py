from app.analytics.elo import EloState


def test_new_team_starts_at_initial_rating():
    elo = EloState()
    assert elo.get(1) == elo.initial_rating
    assert elo.played(1) == 0


def test_winner_gains_rating_and_loser_loses_it():
    elo = EloState()
    elo.record_match(1, 2, home_goals=2, away_goals=0)

    assert elo.get(1) > elo.initial_rating
    assert elo.get(2) < elo.initial_rating
    assert elo.played(1) == 1
    assert elo.played(2) == 1


def test_draw_with_equal_ratings_costs_home_side_a_little():
    elo = EloState()
    elo.record_match(1, 2, home_goals=1, away_goals=1)

    # Home still carries the home-advantage bonus in "expected", so a draw
    # actually costs the home side a little rating.
    assert elo.get(1) < elo.initial_rating
    assert elo.get(2) > elo.initial_rating


def test_bigger_win_moves_rating_more():
    small_win = EloState()
    small_win.record_match(1, 2, home_goals=1, away_goals=0)

    big_win = EloState()
    big_win.record_match(1, 2, home_goals=4, away_goals=0)

    small_delta = small_win.get(1) - small_win.initial_rating
    big_delta = big_win.get(1) - big_win.initial_rating
    assert big_delta > small_delta


def test_compute_update_does_not_mutate_state():
    elo = EloState()
    before = elo.get(1)
    update = elo.compute_update(1, 2, home_goals=2, away_goals=0)

    assert elo.get(1) == before  # unchanged: compute_update is pure
    assert update.home_before == before
    assert update.home_after > before


def test_apply_update_matches_record_match():
    a = EloState()
    b = EloState()

    update = a.compute_update(1, 2, home_goals=3, away_goals=1)
    a.apply_update(1, 2, update)
    b.record_match(1, 2, home_goals=3, away_goals=1)

    assert a.get(1) == b.get(1)
    assert a.get(2) == b.get(2)
