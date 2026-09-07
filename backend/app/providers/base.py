"""Provider-agnostic interface for football data sources.

The rest of the codebase (discovery, sync, analytics) never talks to
football-data.org (or any other vendor) directly — only to this
``FootballProvider`` interface and the plain dataclasses below. Adding a
second vendor (API-Football, SportMonks, ...) means writing one new class
that implements this interface; nothing else changes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class ProviderArea:
    provider_id: str
    name: str
    code: str | None = None
    continent_hint: str | None = None


@dataclass
class ProviderCompetition:
    provider_id: str
    name: str
    code: str | None
    area_provider_id: str
    area_name: str
    competition_type: str  # LEAGUE, CUP, ... (provider's own vocabulary, normalized by the service layer)
    current_season_provider_id: str | None = None
    number_of_available_seasons: int | None = None
    logo: str | None = None


@dataclass
class ProviderSeason:
    provider_id: str
    year_start: int
    year_end: int
    start_date: date | None = None
    end_date: date | None = None
    current: bool = False


@dataclass
class ProviderTeam:
    provider_id: str
    name: str
    short_name: str | None = None
    code: str | None = None
    logo: str | None = None
    founded: int | None = None
    venue: str | None = None
    country_name: str | None = None


@dataclass
class ProviderMatch:
    provider_id: str
    competition_provider_id: str
    season_provider_id: str | None
    utc_date: datetime
    status: str
    matchday: int | None
    home_team_provider_id: str
    home_team_name: str
    away_team_provider_id: str
    away_team_name: str
    home_goals: int | None
    away_goals: int | None
    winner: str | None


@dataclass
class ProviderStandingRow:
    team_provider_id: str
    team_name: str
    played: int
    won: int
    draw: int
    lost: int
    points: int
    goals_for: int
    goals_against: int


@dataclass
class ProviderStandings:
    competition_provider_id: str
    season_provider_id: str | None
    rows: list[ProviderStandingRow] = field(default_factory=list)


class ProviderError(RuntimeError):
    """Base class for provider failures the service layer must handle
    gracefully (never a raw stack trace to the end user)."""


class ProviderAuthError(ProviderError):
    """Missing or invalid API key."""


class ProviderRateLimitError(ProviderError):
    """Provider throttled us; ``retry_after_seconds`` is a best-effort hint."""

    def __init__(self, message: str, retry_after_seconds: int | None = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class ProviderNotFoundError(ProviderError):
    """The requested resource (team, competition, match) doesn't exist."""


class FootballProvider(ABC):
    """Interface every football data vendor integration must implement."""

    name: str

    @abstractmethod
    def get_areas(self) -> list[ProviderArea]:
        """All geographic areas (countries/continents) known to the provider."""

    @abstractmethod
    def get_competitions(self) -> list[ProviderCompetition]:
        """All competitions currently exposed by the provider — this is the
        list ``CompetitionDiscoveryService`` diffs against our database."""

    @abstractmethod
    def get_seasons(self, competition_provider_id: str) -> list[ProviderSeason]:
        ...

    @abstractmethod
    def get_teams(
        self, competition_provider_id: str, season_provider_id: str | None = None
    ) -> list[ProviderTeam]:
        ...

    @abstractmethod
    def get_matches(
        self,
        competition_provider_id: str,
        season_provider_id: str | None = None,
        status: str | None = None,
    ) -> list[ProviderMatch]:
        ...

    @abstractmethod
    def get_standings(
        self, competition_provider_id: str, season_provider_id: str | None = None
    ) -> ProviderStandings:
        ...

    @abstractmethod
    def get_team_matches(self, team_provider_id: str, status: str | None = None) -> list[ProviderMatch]:
        ...
