"""Tracks per-team home/away scoring records, recent form, and head-to-head
history — replayed chronologically, just like the Elo ratings, so that a
prediction only ever uses information available *before* the match being
predicted.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

FORM_WINDOW = 10
DEFAULT_LEAGUE_AVG_HOME_GOALS = 1.45
DEFAULT_LEAGUE_AVG_AWAY_GOALS = 1.15


@dataclass
class TeamRecord:
    home_matches: int = 0
    home_goals_for: int = 0
    home_goals_against: int = 0
    away_matches: int = 0
    away_goals_for: int = 0
    away_goals_against: int = 0
    # Most recent matches first, regardless of venue: (goals_for, goals_against, points)
    recent: deque = field(default_factory=lambda: deque(maxlen=FORM_WINDOW))

    @property
    def matches_played(self) -> int:
        return self.home_matches + self.away_matches

    @property
    def goals_for(self) -> int:
        return self.home_goals_for + self.away_goals_for

    @property
    def goals_against(self) -> int:
        return self.home_goals_against + self.away_goals_against

    def as_dict(self) -> dict:
        recent = list(self.recent)
        points = sum(p for _, _, p in recent)
        return {
            "matches_played": self.matches_played,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "home": {
                "matches": self.home_matches,
                "goals_for": self.home_goals_for,
                "goals_against": self.home_goals_against,
            },
            "away": {
                "matches": self.away_matches,
                "goals_for": self.away_goals_for,
                "goals_against": self.away_goals_against,
            },
            "recent_form": {
                "matches": len(recent),
                "points_per_match": round(points / len(recent), 2) if recent else None,
                "goals_for_avg": round(sum(g for g, _, _ in recent) / len(recent), 2) if recent else None,
                "goals_against_avg": round(sum(g for _, g, _ in recent) / len(recent), 2) if recent else None,
                "results": ["V" if p == 3 else "N" if p == 1 else "D" for _, _, p in recent],
            },
        }


@dataclass
class TeamStats:
    records: dict[str, TeamRecord] = field(default_factory=dict)
    league_home_goals_total: int = 0
    league_home_matches_total: int = 0
    league_away_goals_total: int = 0
    league_away_matches_total: int = 0
    # key: frozenset({team_a, team_b}) -> list of (home_team, away_team, home_goals, away_goals)
    h2h: dict[frozenset, list[tuple]] = field(default_factory=dict)

    def _record(self, team: str) -> TeamRecord:
        return self.records.setdefault(team, TeamRecord())

    def get(self, team: str) -> TeamRecord | None:
        return self.records.get(team)

    def matches_played(self, team: str) -> int:
        record = self.records.get(team)
        return record.matches_played if record else 0

    def league_avg_home_goals(self) -> float:
        if not self.league_home_matches_total:
            return DEFAULT_LEAGUE_AVG_HOME_GOALS
        return self.league_home_goals_total / self.league_home_matches_total

    def league_avg_away_goals(self) -> float:
        if not self.league_away_matches_total:
            return DEFAULT_LEAGUE_AVG_AWAY_GOALS
        return self.league_away_goals_total / self.league_away_matches_total

    def league_avg_goals_per_match(self) -> float:
        return (self.league_avg_home_goals() + self.league_avg_away_goals()) / 2

    def head_to_head(self, team_a: str, team_b: str) -> list[tuple]:
        return self.h2h.get(frozenset({team_a, team_b}), [])

    def record_match(self, home_team: str, away_team: str, home_goals: int, away_goals: int) -> None:
        home = self._record(home_team)
        away = self._record(away_team)

        home.home_matches += 1
        home.home_goals_for += home_goals
        home.home_goals_against += away_goals

        away.away_matches += 1
        away.away_goals_for += away_goals
        away.away_goals_against += home_goals

        home_points = 3 if home_goals > away_goals else 1 if home_goals == away_goals else 0
        away_points = 3 if away_goals > home_goals else 1 if home_goals == away_goals else 0
        home.recent.appendleft((home_goals, away_goals, home_points))
        away.recent.appendleft((away_goals, home_goals, away_points))

        self.league_home_goals_total += home_goals
        self.league_home_matches_total += 1
        self.league_away_goals_total += away_goals
        self.league_away_matches_total += 1

        key = frozenset({home_team, away_team})
        self.h2h.setdefault(key, []).append((home_team, away_team, home_goals, away_goals))
