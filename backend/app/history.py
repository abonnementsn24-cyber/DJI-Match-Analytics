"""Replays stored matches in chronological order to build up-to-date Elo
ratings and team-stats (form/H2H) trackers.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from .elo import EloRatings
from .models import Match
from .team_stats import TeamStats


def build_state(db: Session) -> tuple[EloRatings, TeamStats]:
    ratings = EloRatings()
    stats = TeamStats()
    matches = db.query(Match).order_by(Match.played_at.asc()).all()
    for match in matches:
        home_name, away_name = match.home_team.name, match.away_team.name
        ratings.record_match(home_name, away_name, match.home_goals, match.away_goals)
        stats.record_match(home_name, away_name, match.home_goals, match.away_goals)
    return ratings, stats


def build_ratings(db: Session) -> EloRatings:
    ratings, _ = build_state(db)
    return ratings
