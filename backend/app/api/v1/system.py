from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...ml.artifact import load_artifact
from ...models.competition import Competition
from ...models.enums import MatchStatus
from ...models.match import Match
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
