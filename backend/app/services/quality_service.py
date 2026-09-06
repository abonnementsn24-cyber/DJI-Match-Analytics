"""Scores how usable a competition's data actually is, so the prediction
engine can refuse to guess rather than invent numbers from thin air.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.competition import Competition
from ..models.enums import DataQuality, MatchStatus
from ..models.match import Match


def recompute_data_quality(db: Session, competition: Competition) -> DataQuality:
    finished = (
        db.query(Match)
        .filter(Match.competition_id == competition.id, Match.status == MatchStatus.FINISHED)
        .count()
    )
    competition.historical_depth = finished

    if finished >= 200:
        quality = DataQuality.A
    elif finished >= 50:
        quality = DataQuality.B
    elif finished >= 10:
        quality = DataQuality.C
    else:
        quality = DataQuality.D

    competition.data_quality = quality
    db.flush()
    return quality
