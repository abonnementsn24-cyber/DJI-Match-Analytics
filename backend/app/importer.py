"""Upserts normalized match dicts (from a connector or a seed script) into the DB."""
from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy.orm import Session

from .models import Match, Team


def _get_or_create_team(db: Session, name: str, external_id: str | None = None) -> Team:
    team = db.query(Team).filter(Team.name == name).one_or_none()
    if team is None:
        team = Team(name=name, external_id=external_id)
        db.add(team)
        db.flush()
    elif external_id and not team.external_id:
        team.external_id = external_id
    return team


def import_matches(db: Session, matches: Iterable[dict[str, Any]]) -> int:
    """Insert matches that aren't already stored (by external_id). Returns count added."""
    added = 0
    for raw in matches:
        external_id = raw.get("external_id")
        if external_id and db.query(Match).filter(Match.external_id == external_id).one_or_none():
            continue

        home_team = _get_or_create_team(db, raw["home_team"], raw.get("home_team_external_id"))
        away_team = _get_or_create_team(db, raw["away_team"], raw.get("away_team_external_id"))

        db.add(
            Match(
                external_id=external_id,
                competition=raw.get("competition", "inconnue"),
                played_at=raw["played_at"],
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                home_goals=raw["home_goals"],
                away_goals=raw["away_goals"],
            )
        )
        added += 1

    db.commit()
    return added
