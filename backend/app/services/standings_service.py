"""Computes a league table from our own synced matches (rather than
calling the provider's live standings endpoint every time) — consistent
with whatever has actually been synced, and available even for providers
that don't expose a standings endpoint at all.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.enums import MatchStatus
from ..models.match import Match
from ..models.team import Team


def compute_standings(db: Session, competition_id: int, season_id: int | None = None) -> list[dict]:
    query = db.query(Match).filter(
        Match.competition_id == competition_id, Match.status == MatchStatus.FINISHED
    )
    if season_id is not None:
        query = query.filter(Match.season_id == season_id)

    table: dict[int, dict] = {}

    def row(team_id: int) -> dict:
        if team_id not in table:
            team = db.get(Team, team_id)
            table[team_id] = {
                "team_id": team_id,
                "team": team.canonical_name if team else "?",
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "points": 0,
            }
        return table[team_id]

    for match in query.all():
        home = row(match.home_team_id)
        away = row(match.away_team_id)

        home["played"] += 1
        away["played"] += 1
        home["goals_for"] += match.home_goals
        home["goals_against"] += match.away_goals
        away["goals_for"] += match.away_goals
        away["goals_against"] += match.home_goals

        if match.home_goals > match.away_goals:
            home["wins"] += 1
            home["points"] += 3
            away["losses"] += 1
        elif match.home_goals < match.away_goals:
            away["wins"] += 1
            away["points"] += 3
            home["losses"] += 1
        else:
            home["draws"] += 1
            away["draws"] += 1
            home["points"] += 1
            away["points"] += 1

    for entry in table.values():
        entry["goal_difference"] = entry["goals_for"] - entry["goals_against"]

    return sorted(
        table.values(), key=lambda e: (-e["points"], -e["goal_difference"], -e["goals_for"])
    )
