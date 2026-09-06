"""Pulls competitions/seasons/teams/matches from a provider into our DB.

Idempotent by design: re-running any of these functions on the same data
never creates duplicates (unique constraints on provider IDs) and safely
updates scores/status on matches that were previously only scheduled.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..core.logging import get_logger
from ..models.competition import Competition, Season
from ..models.enums import MatchStatus, MatchWinner
from ..models.match import Match
from ..models.team import CompetitionSeasonTeam
from ..providers.base import FootballProvider, ProviderError
from .normalization_service import get_or_create_team
from .quality_service import recompute_data_quality

logger = get_logger(__name__)


@dataclass
class SyncReport:
    competition_id: int
    seasons_synced: int = 0
    teams_synced: int = 0
    matches_added: int = 0
    matches_updated: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def as_dict(self) -> dict:
        return {
            "competition_id": self.competition_id,
            "seasons_synced": self.seasons_synced,
            "teams_synced": self.teams_synced,
            "matches_added": self.matches_added,
            "matches_updated": self.matches_updated,
            "errors": self.errors,
        }


def get_competition_by_code(db: Session, provider_name: str, code: str) -> Competition | None:
    return (
        db.query(Competition)
        .filter(Competition.provider == provider_name, Competition.code == code)
        .one_or_none()
    )


def sync_seasons(db: Session, provider: FootballProvider, competition: Competition) -> int:
    seasons = provider.get_seasons(competition.provider_id)
    count = 0
    for s in seasons:
        existing = (
            db.query(Season)
            .filter(Season.competition_id == competition.id, Season.provider_id == s.provider_id)
            .one_or_none()
        )
        if existing is None:
            db.add(
                Season(
                    competition_id=competition.id,
                    provider_id=s.provider_id,
                    year_start=s.year_start,
                    year_end=s.year_end,
                    start_date=s.start_date,
                    end_date=s.end_date,
                    current=s.current,
                )
            )
            count += 1
        else:
            existing.current = s.current
    db.commit()
    return count


def get_season_by_year(db: Session, competition: Competition, year: int) -> Season | None:
    return (
        db.query(Season)
        .filter(Season.competition_id == competition.id, Season.year_start == year)
        .one_or_none()
    )


def get_current_season(db: Session, competition: Competition) -> Season | None:
    return (
        db.query(Season)
        .filter(Season.competition_id == competition.id, Season.current.is_(True))
        .one_or_none()
    )


def sync_teams(
    db: Session, provider: FootballProvider, competition: Competition, season: Season
) -> int:
    teams = provider.get_teams(competition.provider_id, season.provider_id)
    count = 0
    for t in teams:
        team = get_or_create_team(db, provider.name, t)
        link = (
            db.query(CompetitionSeasonTeam)
            .filter(
                CompetitionSeasonTeam.season_id == season.id,
                CompetitionSeasonTeam.team_id == team.id,
            )
            .one_or_none()
        )
        if link is None:
            db.add(
                CompetitionSeasonTeam(
                    competition_id=competition.id, season_id=season.id, team_id=team.id
                )
            )
            count += 1
    db.commit()
    return count


_WINNER_MAP = {
    "HOME_TEAM": MatchWinner.HOME_TEAM,
    "AWAY_TEAM": MatchWinner.AWAY_TEAM,
    "DRAW": MatchWinner.DRAW,
}


def sync_matches(
    db: Session,
    provider: FootballProvider,
    competition: Competition,
    season: Season | None = None,
    status: str | None = None,
) -> tuple[int, int]:
    matches = provider.get_matches(
        competition.provider_id,
        season.provider_id if season else None,
        status=status,
    )

    added = 0
    updated = 0
    now = datetime.datetime.utcnow()

    for m in matches:
        home_team = get_or_create_team(
            db,
            provider.name,
            _team_stub(m.home_team_provider_id, m.home_team_name),
        )
        away_team = get_or_create_team(
            db,
            provider.name,
            _team_stub(m.away_team_provider_id, m.away_team_name),
        )

        existing = (
            db.query(Match)
            .filter(Match.provider == provider.name, Match.provider_id == m.provider_id)
            .one_or_none()
        )
        match_status = MatchStatus(m.status) if m.status in MatchStatus.__members__ else MatchStatus.SCHEDULED
        winner = _WINNER_MAP.get(m.winner) if m.winner else None

        if existing is None:
            db.add(
                Match(
                    provider=provider.name,
                    provider_id=m.provider_id,
                    competition_id=competition.id,
                    season_id=season.id if season else None,
                    utc_date=m.utc_date,
                    status=match_status,
                    matchday=m.matchday,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    home_goals=m.home_goals,
                    away_goals=m.away_goals,
                    winner=winner,
                    last_synced_at=now,
                )
            )
            added += 1
        else:
            existing.status = match_status
            existing.home_goals = m.home_goals
            existing.away_goals = m.away_goals
            existing.winner = winner
            existing.last_synced_at = now
            updated += 1

    db.commit()
    recompute_data_quality(db, competition)
    db.commit()
    return added, updated


def _team_stub(provider_id: str, name: str):
    from ..providers.base import ProviderTeam

    return ProviderTeam(provider_id=provider_id, name=name)


def sync_competition(
    db: Session, provider: FootballProvider, code: str, season_year: int | None = None
) -> SyncReport:
    competition = get_competition_by_code(db, provider.name, code)
    if competition is None:
        raise ValueError(
            f"Compétition inconnue: {code!r}. Lancez d'abord la découverte "
            "(`python -m app.cli discover`)."
        )

    report = SyncReport(competition_id=competition.id)

    try:
        report.seasons_synced = sync_seasons(db, provider, competition)

        season = (
            get_season_by_year(db, competition, season_year)
            if season_year
            else get_current_season(db, competition)
        )
        if season is None:
            report.errors.append(
                f"Aucune saison trouvée pour {code} "
                f"({'année ' + str(season_year) if season_year else 'saison courante'})."
            )
            return report

        report.teams_synced = sync_teams(db, provider, competition, season)
        added, updated = sync_matches(db, provider, competition, season)
        report.matches_added = added
        report.matches_updated = updated

    except ProviderError as exc:
        logger.warning("Sync error for %s: %s", code, exc)
        report.errors.append(str(exc))

    return report
