"""football-data.org (API v4) provider.

Notes learned by probing the live API (see docs/DATA_PIPELINE.md):
- ``GET /v4/competitions`` and ``/v4/areas`` work even *without* an API key
  (anonymous access), which is what makes competition discovery possible
  before a user ever configures ``FOOTBALL_DATA_API_KEY``.
- Everything else (teams, matches, standings) requires a valid key and
  returns 403 otherwise — surfaced here as ``ProviderAuthError``.
- The API is rate-limited; the response carries an
  ``X-Requests-Available`` header we read to back off proactively, and a
  429 is mapped to ``ProviderRateLimitError``.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import requests

from ..core.config import get_settings
from ..core.logging import get_logger
from .base import (
    FootballProvider,
    ProviderArea,
    ProviderAuthError,
    ProviderCompetition,
    ProviderMatch,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderSeason,
    ProviderStandingRow,
    ProviderStandings,
    ProviderTeam,
)

logger = get_logger(__name__)

REQUEST_TIMEOUT_SECONDS = 20
MIN_REQUESTS_AVAILABLE_BEFORE_THROTTLE = 2
THROTTLE_SLEEP_SECONDS = 6


def _parse_date(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value).date()


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class FootballDataProvider(FootballProvider):
    name = "football-data"
    base_url = "https://api.football-data.org/v4"

    def __init__(self, api_key: str | None = None, session: requests.Session | None = None):
        self.api_key = api_key if api_key is not None else get_settings().football_data_api_key
        self.session = session or requests.Session()

    def _headers(self) -> dict[str, str]:
        headers = {}
        if self.api_key:
            headers["X-Auth-Token"] = self.api_key
        return headers

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        response = self.session.get(
            f"{self.base_url}{path}",
            headers=self._headers(),
            params={k: v for k, v in (params or {}).items() if v is not None},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        remaining = response.headers.get("X-Requests-Available")
        if remaining is not None and remaining.isdigit() and int(remaining) < MIN_REQUESTS_AVAILABLE_BEFORE_THROTTLE:
            logger.info("football-data.org rate limit nearly reached, throttling")
            time.sleep(THROTTLE_SLEEP_SECONDS)

        if response.status_code == 403:
            raise ProviderAuthError(
                "football-data.org a refusé la requête (403) : clé API manquante, "
                "invalide, ou ressource non incluse dans votre offre."
            )
        if response.status_code == 404:
            raise ProviderNotFoundError(f"Ressource introuvable sur football-data.org: {path}")
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise ProviderRateLimitError(
                "Limite de requêtes football-data.org atteinte.",
                retry_after_seconds=int(retry_after) if retry_after and retry_after.isdigit() else None,
            )
        if response.status_code >= 400:
            raise ProviderNotFoundError(
                f"football-data.org a renvoyé {response.status_code} pour {path}: {response.text[:300]}"
            )

        return response.json()

    # -- discovery -----------------------------------------------------

    def get_areas(self) -> list[ProviderArea]:
        payload = self._get("/areas")
        return [
            ProviderArea(provider_id=str(a["id"]), name=a["name"], code=a.get("countryCode"))
            for a in payload.get("areas", [])
        ]

    def get_competitions(self) -> list[ProviderCompetition]:
        payload = self._get("/competitions")
        competitions = []
        for c in payload.get("competitions", []):
            area = c.get("area", {})
            current_season = c.get("currentSeason") or {}
            competitions.append(
                ProviderCompetition(
                    provider_id=str(c["id"]),
                    name=c["name"],
                    code=c.get("code"),
                    area_provider_id=str(area.get("id")),
                    area_name=area.get("name", "Unknown"),
                    competition_type=c.get("type", "LEAGUE"),
                    current_season_provider_id=(
                        str(current_season["id"]) if current_season.get("id") else None
                    ),
                    number_of_available_seasons=c.get("numberOfAvailableSeasons"),
                    logo=c.get("emblem"),
                )
            )
        return competitions

    # -- seasons / teams / matches (require an API key) -----------------

    def get_seasons(self, competition_provider_id: str) -> list[ProviderSeason]:
        payload = self._get(f"/competitions/{competition_provider_id}")
        current_season_id = (payload.get("currentSeason") or {}).get("id")
        seasons = []
        for s in payload.get("seasons", []):
            start = _parse_date(s.get("startDate"))
            end = _parse_date(s.get("endDate"))
            seasons.append(
                ProviderSeason(
                    provider_id=str(s["id"]),
                    year_start=start.year if start else 0,
                    year_end=end.year if end else (start.year if start else 0),
                    start_date=start,
                    end_date=end,
                    current=(s.get("id") == current_season_id),
                )
            )
        return seasons

    def get_teams(
        self, competition_provider_id: str, season_provider_id: str | None = None
    ) -> list[ProviderTeam]:
        payload = self._get(
            f"/competitions/{competition_provider_id}/teams",
            params={"season": season_provider_id},
        )
        teams = []
        for t in payload.get("teams", []):
            teams.append(
                ProviderTeam(
                    provider_id=str(t["id"]),
                    name=t["name"],
                    short_name=t.get("shortName"),
                    code=t.get("tla"),
                    logo=t.get("crest"),
                    founded=t.get("founded"),
                    venue=t.get("venue"),
                    country_name=(t.get("area") or {}).get("name"),
                )
            )
        return teams

    def get_matches(
        self,
        competition_provider_id: str,
        season_provider_id: str | None = None,
        status: str | None = None,
    ) -> list[ProviderMatch]:
        payload = self._get(
            f"/competitions/{competition_provider_id}/matches",
            params={"season": season_provider_id, "status": status},
        )
        return [self._parse_match(m, competition_provider_id) for m in payload.get("matches", [])]

    def get_team_matches(self, team_provider_id: str, status: str | None = None) -> list[ProviderMatch]:
        payload = self._get(f"/teams/{team_provider_id}/matches", params={"status": status})
        return [
            self._parse_match(m, str(m.get("competition", {}).get("id", "")))
            for m in payload.get("matches", [])
        ]

    def get_standings(
        self, competition_provider_id: str, season_provider_id: str | None = None
    ) -> ProviderStandings:
        payload = self._get(
            f"/competitions/{competition_provider_id}/standings",
            params={"season": season_provider_id},
        )
        rows: list[ProviderStandingRow] = []
        for block in payload.get("standings", []):
            if block.get("type") != "TOTAL":
                continue
            for row in block.get("table", []):
                team = row.get("team", {})
                rows.append(
                    ProviderStandingRow(
                        team_provider_id=str(team.get("id")),
                        team_name=team.get("name", "?"),
                        played=row.get("playedGames", 0),
                        won=row.get("won", 0),
                        draw=row.get("draw", 0),
                        lost=row.get("lost", 0),
                        points=row.get("points", 0),
                        goals_for=row.get("goalsFor", 0),
                        goals_against=row.get("goalsAgainst", 0),
                    )
                )
        season = (payload.get("season") or {}).get("id")
        return ProviderStandings(
            competition_provider_id=competition_provider_id,
            season_provider_id=str(season) if season else season_provider_id,
            rows=rows,
        )

    @staticmethod
    def _parse_match(m: dict, competition_provider_id: str) -> ProviderMatch:
        score = m.get("score", {}).get("fullTime", {})
        season = m.get("season") or {}
        return ProviderMatch(
            provider_id=str(m["id"]),
            competition_provider_id=competition_provider_id,
            season_provider_id=str(season["id"]) if season.get("id") else None,
            utc_date=_parse_datetime(m["utcDate"]),
            status=m.get("status", "SCHEDULED"),
            matchday=m.get("matchday"),
            home_team_provider_id=str(m["homeTeam"]["id"]),
            home_team_name=m["homeTeam"].get("name", "?"),
            away_team_provider_id=str(m["awayTeam"]["id"]),
            away_team_name=m["awayTeam"].get("name", "?"),
            home_goals=score.get("home"),
            away_goals=score.get("away"),
            winner=m.get("score", {}).get("winner"),
        )
