"""Connector for football-data.org (API v4).

Fetches finished matches for a competition/season and normalizes them into
the shape the rest of the app expects. Requires a free API key from
https://www.football-data.org/ set as the FOOTBALL_DATA_API_KEY environment
variable.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests

API_BASE_URL = "https://api.football-data.org/v4"
REQUEST_TIMEOUT_SECONDS = 15


class FootballDataError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.environ.get("FOOTBALL_DATA_API_KEY")
    if not key:
        raise FootballDataError(
            "FOOTBALL_DATA_API_KEY n'est pas configurée. Créez une clé gratuite sur "
            "https://www.football-data.org/ et exportez-la dans l'environnement."
        )
    return key


def fetch_finished_matches(competition_code: str, season: int | None = None) -> list[dict[str, Any]]:
    """Return normalized finished matches for a competition (e.g. "PL", "CL").

    ``season`` is the starting year of the season (e.g. 2023 for 2023/24).
    """
    params: dict[str, Any] = {"status": "FINISHED"}
    if season is not None:
        params["season"] = season

    response = requests.get(
        f"{API_BASE_URL}/competitions/{competition_code}/matches",
        headers={"X-Auth-Token": _api_key()},
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise FootballDataError(
            f"football-data.org a renvoyé {response.status_code}: {response.text}"
        )

    payload = response.json()
    matches = []
    for raw in payload.get("matches", []):
        score = raw.get("score", {}).get("fullTime", {})
        home_goals, away_goals = score.get("home"), score.get("away")
        if home_goals is None or away_goals is None:
            continue
        matches.append(
            {
                "external_id": str(raw["id"]),
                "competition": raw.get("competition", {}).get("name", competition_code),
                "played_at": datetime.fromisoformat(raw["utcDate"].replace("Z", "+00:00")),
                "home_team": raw["homeTeam"]["name"],
                "home_team_external_id": str(raw["homeTeam"]["id"]),
                "away_team": raw["awayTeam"]["name"],
                "away_team_external_id": str(raw["awayTeam"]["id"]),
                "home_goals": home_goals,
                "away_goals": away_goals,
            }
        )
    return matches
