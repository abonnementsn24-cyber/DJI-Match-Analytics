"""Shared test data builders."""
from __future__ import annotations

import datetime
import random

from app.models.competition import Competition
from app.models.enums import MatchWinner
from app.models.match import Match
from app.models.team import Team


def seed_league(db, n_teams=6, n_rounds=4, code="B1", seed=7):
    random.seed(seed)
    competition = Competition(provider="test", provider_id=code, canonical_name=f"League {code}", code=code)
    db.add(competition)
    db.flush()

    teams = []
    for i in range(n_teams):
        team = Team(canonical_name=f"{code} Team {i}")
        db.add(team)
        db.flush()
        teams.append(team)

    start = datetime.datetime(2024, 1, 1)
    index = 0
    for _round in range(n_rounds):
        for home in teams:
            for away in teams:
                if home.id == away.id:
                    continue
                home_goals = random.randint(0, 3)
                away_goals = random.randint(0, 3)
                winner = (
                    MatchWinner.HOME_TEAM if home_goals > away_goals
                    else MatchWinner.AWAY_TEAM if away_goals > home_goals
                    else MatchWinner.DRAW
                )
                db.add(
                    Match(
                        provider="test",
                        provider_id=f"{code}-{index}",
                        competition_id=competition.id,
                        utc_date=start + datetime.timedelta(days=index),
                        status="FINISHED",
                        home_team_id=home.id,
                        away_team_id=away.id,
                        home_goals=home_goals,
                        away_goals=away_goals,
                        winner=winner,
                        last_synced_at=datetime.datetime.utcnow(),
                    )
                )
                index += 1
    db.commit()
    return competition
