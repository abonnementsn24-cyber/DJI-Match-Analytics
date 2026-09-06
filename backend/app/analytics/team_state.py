"""Chronological per-team state: recent form (general, home-only,
away-only), full-history home/away scoring records, head-to-head history,
and days of rest — everything the model variants read from, always as it
stood *before* the match being predicted.
"""
from __future__ import annotations

import datetime
from collections import deque
from dataclasses import dataclass, field

from ..core.config import get_settings

DEFAULT_LEAGUE_AVG_HOME_GOALS = 1.45
DEFAULT_LEAGUE_AVG_AWAY_GOALS = 1.15


@dataclass
class _MatchEntry:
    goals_for: int
    goals_against: int
    points: int
    date: datetime.datetime


@dataclass
class TeamRecord:
    home_matches: int = 0
    home_goals_for: int = 0
    home_goals_against: int = 0
    away_matches: int = 0
    away_goals_for: int = 0
    away_goals_against: int = 0

    overall_recent: deque = field(default_factory=lambda: deque(maxlen=10))
    home_recent: deque = field(default_factory=lambda: deque(maxlen=10))
    away_recent: deque = field(default_factory=lambda: deque(maxlen=10))
    last_match_date: datetime.datetime | None = None

    @property
    def matches_played(self) -> int:
        return self.home_matches + self.away_matches

    @property
    def goals_for(self) -> int:
        return self.home_goals_for + self.away_goals_for

    @property
    def goals_against(self) -> int:
        return self.home_goals_against + self.away_goals_against

    def _form_summary(self, entries: list[_MatchEntry]) -> dict | None:
        if not entries:
            return None
        n = len(entries)
        wins = sum(1 for e in entries if e.points == 3)
        draws = sum(1 for e in entries if e.points == 1)
        losses = n - wins - draws
        goals_for = sum(e.goals_for for e in entries)
        goals_against = sum(e.goals_against for e in entries)
        clean_sheets = sum(1 for e in entries if e.goals_against == 0)
        failed_to_score = sum(1 for e in entries if e.goals_for == 0)
        points = sum(e.points for e in entries)
        return {
            "matches": n,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "points": points,
            "points_per_match": round(points / n, 2),
            "goals_for": goals_for,
            "goals_against": goals_against,
            "avg_goals_for": round(goals_for / n, 2),
            "avg_goals_against": round(goals_against / n, 2),
            "goal_difference": goals_for - goals_against,
            "clean_sheets": clean_sheets,
            "failed_to_score": failed_to_score,
        }

    def form(self, window: int, venue: str = "overall") -> dict | None:
        source = {"overall": self.overall_recent, "home": self.home_recent, "away": self.away_recent}[venue]
        entries = list(source)[:window]
        return self._form_summary(entries)

    def rest_days(self, as_of: datetime.datetime) -> int | None:
        if self.last_match_date is None:
            return None
        return (as_of - self.last_match_date).days

    def as_dict(self) -> dict:
        settings = get_settings()
        short, long = settings.form_window_short, settings.form_window_long
        return {
            "matches_played": self.matches_played,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "home": {"matches": self.home_matches, "goals_for": self.home_goals_for, "goals_against": self.home_goals_against},
            "away": {"matches": self.away_matches, "goals_for": self.away_goals_for, "goals_against": self.away_goals_against},
            "form": {
                f"last_{short}": self.form(short, "overall"),
                f"last_{long}": self.form(long, "overall"),
                f"last_{short}_home": self.form(short, "home"),
                f"last_{long}_home": self.form(long, "home"),
                f"last_{short}_away": self.form(short, "away"),
                f"last_{long}_away": self.form(long, "away"),
            },
        }


@dataclass
class LeagueState:
    """Tracks every team plus league-wide scoring averages and head-to-head
    history, replayed chronologically match by match."""

    records: dict[int, TeamRecord] = field(default_factory=dict)
    league_home_goals_total: int = 0
    league_home_matches_total: int = 0
    league_away_goals_total: int = 0
    league_away_matches_total: int = 0
    h2h: dict[frozenset, list[tuple]] = field(default_factory=dict)  # frozenset({a,b}) -> [(home_id, away_id, hg, ag, date)]

    def _record(self, team_id: int) -> TeamRecord:
        return self.records.setdefault(team_id, TeamRecord())

    def get(self, team_id: int) -> TeamRecord | None:
        return self.records.get(team_id)

    def matches_played(self, team_id: int) -> int:
        record = self.records.get(team_id)
        return record.matches_played if record else 0

    def league_avg_home_goals(self) -> float:
        if not self.league_home_matches_total:
            return DEFAULT_LEAGUE_AVG_HOME_GOALS
        # A real (if extreme) run of shutouts can make the observed average
        # exactly 0 — every attack/defense ratio in model_variants.py divides
        # by this, so floor it rather than propagating a ZeroDivisionError.
        return self.league_home_goals_total / self.league_home_matches_total or DEFAULT_LEAGUE_AVG_HOME_GOALS

    def league_avg_away_goals(self) -> float:
        if not self.league_away_matches_total:
            return DEFAULT_LEAGUE_AVG_AWAY_GOALS
        return self.league_away_goals_total / self.league_away_matches_total or DEFAULT_LEAGUE_AVG_AWAY_GOALS

    def league_avg_goals_per_match(self) -> float:
        return (self.league_avg_home_goals() + self.league_avg_away_goals()) / 2

    def head_to_head(self, team_a: int, team_b: int, max_matches: int | None = None) -> list[tuple]:
        max_matches = max_matches or get_settings().h2h_max_matches
        meetings = self.h2h.get(frozenset({team_a, team_b}), [])
        return meetings[-max_matches:]

    def rest_days_for(self, team_id: int, as_of: datetime.datetime) -> int | None:
        record = self.records.get(team_id)
        return record.rest_days(as_of) if record else None

    def record_match(
        self,
        home_id: int,
        away_id: int,
        home_goals: int,
        away_goals: int,
        date: datetime.datetime,
    ) -> None:
        home = self._record(home_id)
        away = self._record(away_id)

        home.home_matches += 1
        home.home_goals_for += home_goals
        home.home_goals_against += away_goals

        away.away_matches += 1
        away.away_goals_for += away_goals
        away.away_goals_against += home_goals

        home_points = 3 if home_goals > away_goals else 1 if home_goals == away_goals else 0
        away_points = 3 if away_goals > home_goals else 1 if home_goals == away_goals else 0

        home_entry = _MatchEntry(home_goals, away_goals, home_points, date)
        away_entry = _MatchEntry(away_goals, home_goals, away_points, date)

        home.overall_recent.appendleft(home_entry)
        home.home_recent.appendleft(home_entry)
        away.overall_recent.appendleft(away_entry)
        away.away_recent.appendleft(away_entry)

        home.last_match_date = date
        away.last_match_date = date

        self.league_home_goals_total += home_goals
        self.league_home_matches_total += 1
        self.league_away_goals_total += away_goals
        self.league_away_matches_total += 1

        key = frozenset({home_id, away_id})
        self.h2h.setdefault(key, []).append((home_id, away_id, home_goals, away_goals, date))
