"""Seeds the local database with synthetic demo matches.

This is fabricated data (not real results) meant only to let the API and
dashboard be exercised end-to-end without needing a football-data.org API
key. Use `backend/app/connectors/football_data.py` via the `/data/import/*`
endpoint to load real historical matches instead.

Usage: python scripts/seed_sample_data.py
"""
from __future__ import annotations

import datetime
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal, init_db  # noqa: E402
from app.importer import import_matches  # noqa: E402

random.seed(42)

TEAMS = {
    "Dakar FC": 1.35,
    "Thies United": 1.05,
    "Saint-Louis SC": 0.95,
    "Ziguinchor AC": 1.15,
    "Kaolack City": 0.85,
    "Diourbel FC": 1.0,
}
SEASONS = 5
COMPETITION = "Ligue Démo"


def sample_poisson(lam: float) -> int:
    l = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= random.random()
        if p <= l:
            return k - 1


def generate_matches() -> list[dict]:
    names = list(TEAMS)
    matches = []
    start = datetime.datetime(2021, 8, 1)
    match_index = 0

    for season in range(SEASONS):
        for home in names:
            for away in names:
                if home == away:
                    continue
                home_strength = TEAMS[home]
                away_strength = TEAMS[away]
                lam_home = 1.35 * (home_strength / away_strength) ** 0.5
                lam_away = 1.0 * (away_strength / home_strength) ** 0.5

                home_goals = sample_poisson(lam_home)
                away_goals = sample_poisson(lam_away)
                played_at = start + datetime.timedelta(days=match_index * 3)
                match_index += 1

                matches.append(
                    {
                        "external_id": f"demo-{season}-{home}-{away}",
                        "competition": COMPETITION,
                        "played_at": played_at,
                        "home_team": home,
                        "away_team": away,
                        "home_goals": home_goals,
                        "away_goals": away_goals,
                    }
                )
    return matches


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        matches = generate_matches()
        added = import_matches(db, matches)
        print(f"{added} matchs de démonstration ajoutés ({len(matches)} générés).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
