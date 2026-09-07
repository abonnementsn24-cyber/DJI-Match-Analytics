"""A fully in-memory fake provider for tests — no network calls, so
discovery/sync tests never depend on football-data.org being reachable or
on a real API key.
"""
from __future__ import annotations

from datetime import date, datetime

from app.providers.base import (
    FootballProvider,
    ProviderArea,
    ProviderCompetition,
    ProviderMatch,
    ProviderSeason,
    ProviderStandingRow,
    ProviderStandings,
    ProviderTeam,
)


class FakeProvider(FootballProvider):
    name = "fake"

    def __init__(self):
        self.competitions = [
            ProviderCompetition(
                provider_id="1",
                name="Fake League",
                code="FL",
                area_provider_id="10",
                area_name="Senegal",
                competition_type="LEAGUE",
                current_season_provider_id="100",
            )
        ]
        self.seasons = {
            "1": [
                ProviderSeason(
                    provider_id="100", year_start=2024, year_end=2025,
                    start_date=date(2024, 8, 1), end_date=date(2025, 5, 31), current=True,
                )
            ]
        }
        self.teams = {
            "1": [
                ProviderTeam(provider_id="T1", name="Fake FC"),
                ProviderTeam(provider_id="T2", name="Fake United"),
            ]
        }
        self.matches = {
            "1": [
                ProviderMatch(
                    provider_id="M1",
                    competition_provider_id="1",
                    season_provider_id="100",
                    utc_date=datetime(2024, 9, 1, 18, 0),
                    status="FINISHED",
                    matchday=1,
                    home_team_provider_id="T1",
                    home_team_name="Fake FC",
                    away_team_provider_id="T2",
                    away_team_name="Fake United",
                    home_goals=2,
                    away_goals=1,
                    winner="HOME_TEAM",
                )
            ]
        }

    def get_areas(self) -> list[ProviderArea]:
        return [ProviderArea(provider_id="10", name="Senegal")]

    def get_competitions(self) -> list[ProviderCompetition]:
        return self.competitions

    def get_seasons(self, competition_provider_id: str) -> list[ProviderSeason]:
        return self.seasons.get(competition_provider_id, [])

    def get_teams(self, competition_provider_id, season_provider_id=None):
        return self.teams.get(competition_provider_id, [])

    def get_matches(self, competition_provider_id, season_provider_id=None, status=None):
        matches = self.matches.get(competition_provider_id, [])
        if status:
            matches = [m for m in matches if m.status == status]
        return matches

    def get_standings(self, competition_provider_id, season_provider_id=None) -> ProviderStandings:
        return ProviderStandings(
            competition_provider_id=competition_provider_id,
            season_provider_id=season_provider_id,
            rows=[
                ProviderStandingRow("T1", "Fake FC", 1, 1, 0, 0, 3, 2, 1),
                ProviderStandingRow("T2", "Fake United", 1, 0, 0, 1, 0, 1, 2),
            ],
        )

    def get_team_matches(self, team_provider_id, status=None):
        return [m for m in self.matches["1"] if team_provider_id in (m.home_team_provider_id, m.away_team_provider_id)]
