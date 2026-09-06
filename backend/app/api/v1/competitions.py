from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ...models.competition import Competition, Season
from ...models.country import Country
from ...models.enums import Continent
from ...models.match import Match
from ...models.team import CompetitionSeasonTeam, Team
from ...services.discovery_service import list_world_tree
from ...services.standings_service import compute_standings
from ..deps import get_db
from .serializers import serialize_competition, serialize_match_summary, serialize_team

router = APIRouter(tags=["competitions"])


@router.get("/competitions")
def competitions_tree(
    continent: Continent | None = None, db: Session = Depends(get_db)
) -> list[dict]:
    """World -> continent -> country -> competitions, built entirely from
    what ``CompetitionDiscoveryService`` has found — never a static list."""
    tree = list_world_tree(db)
    if continent is not None:
        tree = [node for node in tree if node["continent"] == continent.value]
    return tree


@router.get("/competitions/{competition_id}")
def competition_detail(competition_id: int, db: Session = Depends(get_db)) -> dict:
    competition = db.get(Competition, competition_id)
    if competition is None:
        raise HTTPException(status_code=404, detail="Compétition introuvable.")

    seasons = db.query(Season).filter(Season.competition_id == competition_id).all()
    return {
        **serialize_competition(competition),
        "historical_depth": competition.historical_depth,
        "last_sync": competition.last_sync.isoformat() if competition.last_sync else None,
        "seasons": [
            {
                "id": s.id,
                "year_start": s.year_start,
                "year_end": s.year_end,
                "current": s.current,
            }
            for s in seasons
        ],
    }


@router.get("/competitions/{competition_id}/teams")
def competition_teams(competition_id: int, season_id: int | None = None, db: Session = Depends(get_db)) -> list[dict]:
    query = db.query(Team).join(CompetitionSeasonTeam, CompetitionSeasonTeam.team_id == Team.id).filter(
        CompetitionSeasonTeam.competition_id == competition_id
    )
    if season_id is not None:
        query = query.filter(CompetitionSeasonTeam.season_id == season_id)
    return [serialize_team(t) for t in query.all()]


@router.get("/competitions/{competition_id}/standings")
def competition_standings(
    competition_id: int, season_id: int | None = None, db: Session = Depends(get_db)
) -> list[dict]:
    return compute_standings(db, competition_id, season_id)


@router.get("/competitions/{competition_id}/matches")
def competition_matches(
    competition_id: int,
    season_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    query = (
        db.query(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition))
        .filter(Match.competition_id == competition_id)
    )
    if season_id is not None:
        query = query.filter(Match.season_id == season_id)
    if status is not None:
        query = query.filter(Match.status == status)
    matches = query.order_by(Match.utc_date.asc()).all()
    return [serialize_match_summary(m) for m in matches]


@router.get("/countries/{country_id}")
def country_detail(country_id: int, db: Session = Depends(get_db)) -> dict:
    country = db.get(Country, country_id)
    if country is None:
        raise HTTPException(status_code=404, detail="Pays introuvable.")

    competitions = db.query(Competition).filter(Competition.country_id == country_id).all()
    return {
        "id": country.id,
        "name": country.name,
        "continent": country.continent.value,
        "competitions": [serialize_competition(c) for c in competitions],
    }
