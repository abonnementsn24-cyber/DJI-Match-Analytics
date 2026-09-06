from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...analytics.replay_engine import build_current_state
from ...models.team import CompetitionSeasonTeam, Team
from ..deps import get_db
from .serializers import serialize_team

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("")
def list_teams(
    search: str | None = Query(None, description="Recherche par nom"),
    competition_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Team)
    if competition_id is not None:
        query = query.join(
            CompetitionSeasonTeam, CompetitionSeasonTeam.team_id == Team.id
        ).filter(CompetitionSeasonTeam.competition_id == competition_id)
    if search:
        query = query.filter(Team.canonical_name.ilike(f"%{search}%"))

    total = query.count()
    teams = query.order_by(Team.canonical_name.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "results": [serialize_team(t) for t in teams],
    }


@router.get("/{team_id}")
def team_detail(team_id: int, db: Session = Depends(get_db)) -> dict:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Équipe introuvable.")
    return serialize_team(team)


@router.get("/{team_id}/form")
def team_form(team_id: int, db: Session = Depends(get_db)) -> dict:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Équipe introuvable.")

    state, elo = build_current_state(db)
    record = state.get(team_id)
    if record is None:
        return {
            "team": serialize_team(team),
            "reliable": False,
            "reason": "Aucun historique de matchs disponible pour cette équipe.",
        }

    return {
        "team": serialize_team(team),
        "reliable": True,
        "elo_rating": round(elo.get(team_id), 1),
        **record.as_dict(),
    }
