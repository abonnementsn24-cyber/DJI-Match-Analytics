from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...ml.artifact import load_artifact
from ...models.competition import Competition
from ...models.enums import MatchStatus
from ...models.match import Match
from ...services.popular_leagues import POPULAR_LEAGUES, UNAVAILABLE_FROM_PROVIDER
from ..deps import get_db

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
def system_status(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    demo_matches = db.query(func.count(Match.id)).filter(Match.provider == "demo").scalar() or 0
    real_matches = db.query(func.count(Match.id)).filter(Match.provider != "demo").scalar() or 0

    return {
        "demo_mode": settings.demo_mode,
        "provider_configured": not settings.demo_mode,
        "competitions_count": db.query(func.count(Competition.id)).scalar() or 0,
        "matches_count": demo_matches + real_matches,
        "demo_matches_count": demo_matches,
        "real_matches_count": real_matches,
        "finished_matches_count": (
            db.query(func.count(Match.id)).filter(Match.status == MatchStatus.FINISHED).scalar() or 0
        ),
        "ml_model_available": load_artifact() is not None,
    }


@router.get("/popular-leagues")
def popular_leagues(db: Session = Depends(get_db)) -> dict:
    """The priority list the automatic scheduler keeps in sync — see
    app/services/popular_leagues.py. Includes leagues that are requested
    often but not available from the currently configured provider(s),
    so the gap is visible rather than silently absent.
    """
    leagues = []
    for league in POPULAR_LEAGUES:
        competition = (
            db.query(Competition)
            .filter(Competition.provider == "football-data", Competition.code == league.code)
            .one_or_none()
        )
        leagues.append(
            {
                "code": league.code,
                "label": league.label,
                "country": league.country,
                "synced": competition is not None and competition.last_sync is not None,
                "competition_id": competition.id if competition else None,
                "last_sync": competition.last_sync.isoformat() if competition and competition.last_sync else None,
                "data_quality": competition.data_quality.value if competition else None,
            }
        )

    return {"leagues": leagues, "unavailable": list(UNAVAILABLE_FROM_PROVIDER)}
