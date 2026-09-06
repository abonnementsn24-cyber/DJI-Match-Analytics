"""Poisson scoreline model, calibrated from Elo ratings.

The approach:
1. Start from league-average expected goals for a home / away team.
2. Scale those by the Elo rating gap between the two sides (an exponential
   function of the rating difference, so a bigger gap means a bigger swing).
3. Build the full scoreline probability matrix P(home=i, away=j) using
   independent Poisson distributions, with a small Dixon-Coles style
   correction on the low-scoring cells (0-0, 1-0, 0-1, 1-1) since real
   matches are slightly less independent there than plain Poisson assumes.
4. Derive 1/N/2, BTTS, over/under and the most likely scorelines from that
   matrix.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MAX_GOALS = 8

# League-wide averages used as the neutral starting point before Elo
# adjustment. Roughly matches typical major-league scoring rates.
LEAGUE_AVG_HOME_GOALS = 1.45
LEAGUE_AVG_AWAY_GOALS = 1.15

# How strongly an Elo gap moves expected goals. 400 Elo points is the
# classic "10x more likely to win" gap; RATING_SCALE controls how much of
# that translates into goals rather than pure win probability.
RATING_SCALE = 400.0
GOAL_SENSITIVITY = 0.42

# Dixon-Coles low-score correlation term (small negative value = football's
# real-world tendency for slightly fewer 0-0/1-1 draws than pure Poisson).
DIXON_COLES_RHO = -0.06


def _poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def _dixon_coles_tau(home_goals: int, away_goals: int, lam_home: float, lam_away: float, rho: float) -> float:
    if home_goals == 0 and away_goals == 0:
        return 1 - lam_home * lam_away * rho
    if home_goals == 0 and away_goals == 1:
        return 1 + lam_home * rho
    if home_goals == 1 and away_goals == 0:
        return 1 + lam_away * rho
    if home_goals == 1 and away_goals == 1:
        return 1 - rho
    return 1.0


def expected_goals(home_rating: float, away_rating: float) -> tuple[float, float]:
    """Return (expected_home_goals, expected_away_goals) for the matchup."""
    diff = home_rating - away_rating
    home_factor = math.exp(GOAL_SENSITIVITY * diff / RATING_SCALE)
    away_factor = math.exp(-GOAL_SENSITIVITY * diff / RATING_SCALE)
    lam_home = LEAGUE_AVG_HOME_GOALS * home_factor
    lam_away = LEAGUE_AVG_AWAY_GOALS * away_factor
    return lam_home, lam_away


def score_matrix(lam_home: float, lam_away: float, max_goals: int = MAX_GOALS) -> list[list[float]]:
    """P(home scores i, away scores j) for i, j in [0, max_goals]."""
    matrix = [
        [_poisson_pmf(i, lam_home) * _poisson_pmf(j, lam_away) for j in range(max_goals + 1)]
        for i in range(max_goals + 1)
    ]
    for i in range(min(2, max_goals) + 1):
        for j in range(min(2, max_goals) + 1):
            matrix[i][j] *= _dixon_coles_tau(i, j, lam_home, lam_away, DIXON_COLES_RHO)

    total = sum(sum(row) for row in matrix)
    return [[cell / total for cell in row] for row in matrix]


@dataclass
class MatchProbabilities:
    home_win: float
    draw: float
    away_win: float
    btts: float
    over_2_5: float
    expected_home_goals: float
    expected_away_goals: float
    top_scores: list[tuple[tuple[int, int], float]]

    def as_dict(self) -> dict:
        return {
            "home_win": round(self.home_win, 4),
            "draw": round(self.draw, 4),
            "away_win": round(self.away_win, 4),
            "btts": round(self.btts, 4),
            "over_2_5": round(self.over_2_5, 4),
            "expected_home_goals": round(self.expected_home_goals, 2),
            "expected_away_goals": round(self.expected_away_goals, 2),
            "top_scores": [
                {"score": f"{h}-{a}", "probability": round(p, 4)} for (h, a), p in self.top_scores
            ],
        }


def predict_from_matrix(matrix: list[list[float]], lam_home: float, lam_away: float) -> MatchProbabilities:
    size = len(matrix)
    home_win = draw = away_win = btts = over_2_5 = 0.0
    scores: list[tuple[tuple[int, int], float]] = []

    for i in range(size):
        for j in range(size):
            p = matrix[i][j]
            scores.append(((i, j), p))
            if i > j:
                home_win += p
            elif i < j:
                away_win += p
            else:
                draw += p
            if i >= 1 and j >= 1:
                btts += p
            if i + j >= 3:
                over_2_5 += p

    scores.sort(key=lambda item: item[1], reverse=True)

    return MatchProbabilities(
        home_win=home_win,
        draw=draw,
        away_win=away_win,
        btts=btts,
        over_2_5=over_2_5,
        expected_home_goals=lam_home,
        expected_away_goals=lam_away,
        top_scores=scores[:3],
    )


def predict_match(home_rating: float, away_rating: float) -> MatchProbabilities:
    lam_home, lam_away = expected_goals(home_rating, away_rating)
    matrix = score_matrix(lam_home, lam_away)
    return predict_from_matrix(matrix, lam_home, lam_away)
