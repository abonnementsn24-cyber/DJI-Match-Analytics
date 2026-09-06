"""Replays stored matches in chronological order to build up-to-date Elo ratings."""
from __future__ import annotations

from sqlalchemy.orm import Session

from .elo import EloRatings
from .models import Match


def build_ratings(db: Session) -> EloRatings:
    ratings = EloRatings()
    matches = db.query(Match).order_by(Match.played_at.asc()).all()
    for match in matches:
        ratings.record_match(
            match.home_team.name, match.away_team.name, match.home_goals, match.away_goals
        )
    return ratings
