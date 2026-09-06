"""Seeds fabricated demo matches across three continents so the API and
dashboard can be exercised end-to-end without a football-data.org API key.

Every competition/team name is prefixed "DEMO -" so it can never be
mistaken for real data — the frontend reads this to show a "Mode démo"
banner instead of "Données réelles". Real data always comes from
``python -m app.cli discover`` + ``sync`` once FOOTBALL_DATA_API_KEY is set.

Usage: python scripts/seed_demo_data.py
"""
from __future__ import annotations

import datetime
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db.session import SessionLocal, init_db
from app.models.competition import Competition, Season
from app.models.country import Country
from app.models.enums import (
    CompetitionType,
    Continent,
    MatchStatus,
    MatchWinner,
)
from app.models.match import Match
from app.models.team import CompetitionSeasonTeam, Team
from app.services.quality_service import recompute_data_quality

random.seed(42)

LEAGUES = [
    {
        "country": "Senegal",
        "continent": Continent.AFRICA,
        "competition": "DEMO - Ligue 1 Sénégal",
        "code": "DEMO-SN1",
        "teams": {
            "Dakar FC": 1.35, "Thies United": 1.05, "Saint-Louis SC": 0.95,
            "Ziguinchor AC": 1.15, "Kaolack City": 0.85, "Diourbel FC": 1.0,
        },
    },
    {
        "country": "England",
        "continent": Continent.EUROPE,
        "competition": "DEMO - Premier Division",
        "code": "DEMO-EN1",
        "teams": {
            "Northgate United": 1.5, "Riverside Athletic": 1.2, "Old Mill Town": 0.9,
            "Harborview FC": 1.1, "Kingsbridge Rovers": 0.8, "Eastfield Wanderers": 1.0,
        },
    },
    {
        "country": "Brazil",
        "continent": Continent.SOUTH_AMERICA,
        "competition": "DEMO - Serie Sul",
        "code": "DEMO-BR1",
        "teams": {
            "Costa Verde EC": 1.4, "Serra Azul FC": 1.0, "Praia Alta SC": 0.9,
            "Vale Dourado AC": 1.2, "Rio Claro United": 0.85, "Monte Alegre FC": 0.95,
        },
    },
]

SEASONS = 4


def sample_poisson(lam: float) -> int:
    threshold = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= random.random()
        if p <= threshold:
            return k - 1


def seed_league(db, league: dict, match_index_start: int) -> int:
    country = db.query(Country).filter(Country.name == league["country"]).one_or_none()
    if country is None:
        country = Country(name=league["country"], continent=league["continent"])
        db.add(country)
        db.flush()

    competition = (
        db.query(Competition)
        .filter(Competition.provider == "demo", Competition.code == league["code"])
        .one_or_none()
    )
    if competition is None:
        competition = Competition(
            provider="demo",
            provider_id=league["code"],
            code=league["code"],
            canonical_name=league["competition"],
            country_id=country.id,
            continent=league["continent"],
            competition_type=CompetitionType.LEAGUE,
            active=True,
        )
        db.add(competition)
        db.flush()

    season = (
        db.query(Season)
        .filter(Season.competition_id == competition.id, Season.year_start == 2025)
        .one_or_none()
    )
    if season is None:
        season = Season(
            competition_id=competition.id,
            provider_id=f"{league['code']}-2025",
            year_start=2025,
            year_end=2026,
            current=True,
        )
        db.add(season)
        db.flush()

    teams = {}
    for name, strength in league["teams"].items():
        team = db.query(Team).filter(Team.canonical_name == name).one_or_none()
        if team is None:
            team = Team(canonical_name=name, country_id=country.id)
            db.add(team)
            db.flush()
        teams[name] = (team, strength)

        link = (
            db.query(CompetitionSeasonTeam)
            .filter(CompetitionSeasonTeam.season_id == season.id, CompetitionSeasonTeam.team_id == team.id)
            .one_or_none()
        )
        if link is None:
            db.add(CompetitionSeasonTeam(competition_id=competition.id, season_id=season.id, team_id=team.id))

    db.flush()

    match_index = match_index_start
    start_date = datetime.datetime(2023, 8, 1)
    names = list(teams)

    for _round in range(SEASONS):
        for home_name in names:
            for away_name in names:
                if home_name == away_name:
                    continue
                _, home_strength = teams[home_name]
                _, away_strength = teams[away_name]
                lam_home = 1.35 * (home_strength / away_strength) ** 0.5
                lam_away = 1.0 * (away_strength / home_strength) ** 0.5
                home_goals = sample_poisson(lam_home)
                away_goals = sample_poisson(lam_away)

                external_id = f"demo-{league['code']}-{match_index}"
                existing = db.query(Match).filter(Match.provider == "demo", Match.provider_id == external_id).one_or_none()
                if existing is not None:
                    match_index += 1
                    continue

                winner = (
                    MatchWinner.HOME_TEAM if home_goals > away_goals
                    else MatchWinner.AWAY_TEAM if away_goals > home_goals
                    else MatchWinner.DRAW
                )
                db.add(
                    Match(
                        provider="demo",
                        provider_id=external_id,
                        competition_id=competition.id,
                        season_id=season.id,
                        utc_date=start_date + datetime.timedelta(days=match_index * 3),
                        status=MatchStatus.FINISHED,
                        home_team_id=teams[home_name][0].id,
                        away_team_id=teams[away_name][0].id,
                        home_goals=home_goals,
                        away_goals=away_goals,
                        winner=winner,
                        last_synced_at=datetime.datetime.utcnow(),
                    )
                )
                match_index += 1

    # A handful of upcoming (scheduled, no score yet) fixtures so /matches/today
    # and /matches/upcoming have something to show.
    for i in range(3):
        home_name, away_name = random.sample(names, 2)
        external_id = f"demo-{league['code']}-upcoming-{i}"
        existing = db.query(Match).filter(Match.provider == "demo", Match.provider_id == external_id).one_or_none()
        if existing is None:
            db.add(
                Match(
                    provider="demo",
                    provider_id=external_id,
                    competition_id=competition.id,
                    season_id=season.id,
                    utc_date=datetime.datetime.utcnow() + datetime.timedelta(days=i),
                    status=MatchStatus.SCHEDULED,
                    home_team_id=teams[home_name][0].id,
                    away_team_id=teams[away_name][0].id,
                    home_goals=None,
                    away_goals=None,
                    winner=None,
                )
            )

    db.commit()
    recompute_data_quality(db, competition)
    db.commit()
    return match_index


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        index = 0
        for league in LEAGUES:
            index = seed_league(db, league, index)
        print("Données de démonstration (fictives) chargées pour", len(LEAGUES), "compétitions.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
