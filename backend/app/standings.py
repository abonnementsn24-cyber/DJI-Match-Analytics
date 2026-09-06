"""Computes a simple league table (points, GF/GA/GD) from stored matches."""
from __future__ import annotations

from sqlalchemy.orm import Session

from .models import Match


def compute_standings(db: Session, competition: str | None = None) -> list[dict]:
    query = db.query(Match)
    if competition:
        query = query.filter(Match.competition == competition)

    table: dict[str, dict] = {}

    def row(team: str) -> dict:
        return table.setdefault(
            team,
            {
                "team": team,
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "points": 0,
            },
        )

    for match in query.all():
        home = row(match.home_team.name)
        away = row(match.away_team.name)

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

    return sorted(table.values(), key=lambda e: (-e["points"], -e["goal_difference"], -e["goals_for"]))
