from datetime import datetime

from app.database import SessionLocal, init_db
from app.importer import import_matches
from app.standings import compute_standings


def test_standings_ranks_by_points_then_goal_difference():
    init_db()
    db = SessionLocal()
    try:
        matches = [
            {
                "external_id": "standings-1",
                "competition": "Standings Test League",
                "played_at": datetime(2024, 1, 1),
                "home_team": "Alpha",
                "away_team": "Beta",
                "home_goals": 3,
                "away_goals": 0,
            },
            {
                "external_id": "standings-2",
                "competition": "Standings Test League",
                "played_at": datetime(2024, 1, 8),
                "home_team": "Beta",
                "away_team": "Alpha",
                "home_goals": 1,
                "away_goals": 1,
            },
        ]
        import_matches(db, matches)

        table = compute_standings(db, competition="Standings Test League")
    finally:
        db.close()

    assert table[0]["team"] == "Alpha"
    assert table[0]["points"] == 4
    assert table[0]["goal_difference"] == 3
    assert table[1]["team"] == "Beta"
    assert table[1]["points"] == 1
