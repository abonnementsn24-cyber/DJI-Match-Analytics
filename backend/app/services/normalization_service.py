"""Turns raw provider payloads into our canonical entities, via the mapping
tables — this is the only place that's allowed to create a ``Team`` or
``Competition`` row, and it always goes through a provider-ID mapping
first. Two providers naming the same club differently never get merged
just because the names look alike; they only converge when a human/service
deliberately links their provider IDs to the same canonical row.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.competition import Competition
from ..models.country import Country
from ..models.enums import CompetitionType
from ..models.mapping import ProviderCompetitionMapping, ProviderTeamMapping
from ..models.team import Team
from ..providers.base import ProviderCompetition, ProviderTeam
from .geography import continent_for_area

_COMPETITION_TYPE_MAP = {
    "LEAGUE": CompetitionType.LEAGUE,
    "CUP": CompetitionType.CUP,
    "PLAYOFF": CompetitionType.PLAYOFF,
    "SUPER_CUP": CompetitionType.SUPER_CUP,
    "QUALIFICATION": CompetitionType.QUALIFICATION,
    "INTERNATIONAL": CompetitionType.INTERNATIONAL,
}


def get_or_create_country(db: Session, name: str, code: str | None = None) -> Country:
    country = db.query(Country).filter(Country.name == name).one_or_none()
    if country is None:
        country = Country(name=name, code=code, continent=continent_for_area(name))
        db.add(country)
        db.flush()
    return country


def get_or_create_competition(
    db: Session, provider: str, competition: ProviderCompetition
) -> Competition:
    mapping = (
        db.query(ProviderCompetitionMapping)
        .filter(
            ProviderCompetitionMapping.provider == provider,
            ProviderCompetitionMapping.provider_competition_id == competition.provider_id,
        )
        .one_or_none()
    )
    if mapping is not None:
        row = db.get(Competition, mapping.competition_id)
        if row is not None:
            _update_competition_fields(db, row, competition)
            return row

    country = get_or_create_country(db, competition.area_name)
    row = Competition(
        provider=provider,
        provider_id=competition.provider_id,
        code=competition.code,
        canonical_name=competition.name,
        country_id=country.id,
        continent=continent_for_area(competition.area_name),
        competition_type=_COMPETITION_TYPE_MAP.get(
            competition.competition_type.upper(), CompetitionType.LEAGUE
        ),
        logo=competition.logo,
        active=True,
    )
    db.add(row)
    db.flush()

    db.add(
        ProviderCompetitionMapping(
            provider=provider,
            provider_competition_id=competition.provider_id,
            provider_name=competition.name,
            competition_id=row.id,
        )
    )
    db.flush()
    return row


def _update_competition_fields(db: Session, row: Competition, competition: ProviderCompetition) -> None:
    row.canonical_name = competition.name
    row.code = competition.code
    row.logo = competition.logo or row.logo
    db.flush()


def get_or_create_team(db: Session, provider: str, team: ProviderTeam) -> Team:
    mapping = (
        db.query(ProviderTeamMapping)
        .filter(
            ProviderTeamMapping.provider == provider,
            ProviderTeamMapping.provider_team_id == team.provider_id,
        )
        .one_or_none()
    )
    if mapping is not None:
        row = db.get(Team, mapping.team_id)
        if row is not None:
            return row

    country = get_or_create_country(db, team.country_name) if team.country_name else None
    row = Team(
        canonical_name=team.name,
        short_name=team.short_name,
        code=team.code,
        logo=team.logo,
        country_id=country.id if country else None,
        founded=team.founded,
        venue=team.venue,
    )
    db.add(row)
    db.flush()

    db.add(
        ProviderTeamMapping(
            provider=provider,
            provider_team_id=team.provider_id,
            provider_name=team.name,
            team_id=row.id,
        )
    )
    db.flush()
    return row
