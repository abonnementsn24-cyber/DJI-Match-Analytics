"""Chronological Elo rating engine.

The critical invariant (see docs/DATA_PIPELINE.md §Elo and §Data leakage):
a match's prediction must use the rating as it stood *immediately before*
that match, never a rating recomputed with hindsight. ``EloState`` only
exposes ``get()`` (current, i.e. "as of now in the replay") and
``record_match()`` (advances the state) — there is no way to ask "what was
the rating on date X" except by replaying up to X, which is exactly what
``replay_engine.py`` does.

``compute_update``/``apply_update`` split the pure math from the mutation
so callers that need to persist a before/after snapshot (``EloHistory``)
don't have to duplicate the formula.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..core.config import get_settings


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
class EloUpdate:
    home_before: float
    home_after: float
    away_before: float
    away_after: float


@dataclass
class EloState:
    initial_rating: float = field(default=None)
    home_advantage: float = field(default=None)
    k_factor: float = field(default=None)
    ratings: dict[str, float] = field(default_factory=dict)
    matches_played: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        settings = get_settings()
        if self.initial_rating is None:
            self.initial_rating = settings.elo_initial_rating
        if self.home_advantage is None:
            self.home_advantage = settings.elo_home_advantage
        if self.k_factor is None:
            self.k_factor = settings.elo_k_factor

    def get(self, team_id: int) -> float:
        return self.ratings.get(team_id, self.initial_rating)

    def played(self, team_id: int) -> int:
        return self.matches_played.get(team_id, 0)

    def compute_update(
        self, home_team_id: int, away_team_id: int, home_goals: int, away_goals: int
    ) -> EloUpdate:
        """Pure: computes what the update *would* be, without mutating state."""
        home_before = self.get(home_team_id)
        away_before = self.get(away_team_id)

        expected_home = expected_score(home_before + self.home_advantage, away_before)

        if home_goals > away_goals:
            actual_home = 1.0
        elif home_goals < away_goals:
            actual_home = 0.0
        else:
            actual_home = 0.5

        multiplier = _goal_diff_multiplier(abs(home_goals - away_goals))
        delta = self.k_factor * multiplier * (actual_home - expected_home)

        return EloUpdate(
            home_before=home_before,
            home_after=home_before + delta,
            away_before=away_before,
            away_after=away_before - delta,
        )

    def apply_update(self, home_team_id: int, away_team_id: int, update: EloUpdate) -> None:
        self.ratings[home_team_id] = update.home_after
        self.ratings[away_team_id] = update.away_after
        self.matches_played[home_team_id] = self.played(home_team_id) + 1
        self.matches_played[away_team_id] = self.played(away_team_id) + 1

    def record_match(
        self, home_team_id: int, away_team_id: int, home_goals: int, away_goals: int
    ) -> EloUpdate:
        """Advances the state; returns the applied update."""
        update = self.compute_update(home_team_id, away_team_id, home_goals, away_goals)
        self.apply_update(home_team_id, away_team_id, update)
        return update
