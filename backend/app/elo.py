"""Elo rating engine adapted for football.

Ratings start at ``INITIAL_RATING`` and are updated match by match using the
classic Elo formula, with a home-advantage bonus and a goal-difference
multiplier (teams that win big move their rating further than teams that
scrape a 1-0).
"""
from __future__ import annotations

from dataclasses import dataclass, field

INITIAL_RATING = 1500.0
HOME_ADVANTAGE = 65.0
K_FACTOR = 20.0


def expected_score(rating_a: float, rating_b: float) -> float:
    """Probability that ``a`` beats ``b`` (draws counted as half a win) per Elo."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def _goal_diff_multiplier(goal_diff: int) -> float:
    if goal_diff <= 1:
        return 1.0
    if goal_diff == 2:
        return 1.5
    return (11 + goal_diff) / 8.0


@dataclass
class EloRatings:
    ratings: dict[str, float] = field(default_factory=dict)
    matches_played: dict[str, int] = field(default_factory=dict)

    def get(self, team: str) -> float:
        return self.ratings.get(team, INITIAL_RATING)

    def played(self, team: str) -> int:
        return self.matches_played.get(team, 0)

    def record_match(
        self, home_team: str, away_team: str, home_goals: int, away_goals: int
    ) -> None:
        home_rating = self.get(home_team)
        away_rating = self.get(away_team)

        expected_home = expected_score(home_rating + HOME_ADVANTAGE, away_rating)

        if home_goals > away_goals:
            actual_home = 1.0
        elif home_goals < away_goals:
            actual_home = 0.0
        else:
            actual_home = 0.5

        multiplier = _goal_diff_multiplier(abs(home_goals - away_goals))
        delta = K_FACTOR * multiplier * (actual_home - expected_home)

        self.ratings[home_team] = home_rating + delta
        self.ratings[away_team] = away_rating - delta
        self.matches_played[home_team] = self.played(home_team) + 1
        self.matches_played[away_team] = self.played(away_team) + 1
