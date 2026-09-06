"""Poisson scoreline model shared by every model variant: given expected
goals (however they were computed — league average, form, Elo, ...), build
the full scoreline probability matrix and derive 1/N/2, BTTS, over/under
and the most likely scorelines from it.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MAX_GOALS = 8
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


def score_matrix(lam_home: float, lam_away: float, max_goals: int = MAX_GOALS) -> list[list[float]]:
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
            "home_win_probability": round(self.home_win, 4),
            "draw_probability": round(self.draw, 4),
            "away_win_probability": round(self.away_win, 4),
            "btts_probability": round(self.btts, 4),
            "over_2_5_probability": round(self.over_2_5, 4),
            "expected_home_goals": round(self.expected_home_goals, 2),
            "expected_away_goals": round(self.expected_away_goals, 2),
            "top_scores": [
                {"score": f"{h}-{a}", "probability": round(p, 4)} for (h, a), p in self.top_scores
            ],
        }


def predict_from_matrix(
    matrix: list[list[float]], lam_home: float, lam_away: float, top_n: int = 5
) -> MatchProbabilities:
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
        top_scores=scores[:top_n],
    )


def predict_match(lam_home: float, lam_away: float, top_n: int = 5) -> MatchProbabilities:
    matrix = score_matrix(lam_home, lam_away)
    return predict_from_matrix(matrix, lam_home, lam_away, top_n=top_n)
