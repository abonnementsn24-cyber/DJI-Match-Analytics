from datetime import datetime

from fastapi.testclient import TestClient

from app.database import SessionLocal, init_db
from app.importer import import_matches
from app.main import app

init_db()
client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_reports_insufficient_data_for_unknown_teams():
    response = client.get("/predict", params={"home": "Nowhere FC", "away": "Nobody United"})
    assert response.status_code == 200
    body = response.json()
    assert body["reliable"] is False
    assert "reason" in body


def test_predict_returns_probabilities_once_enough_matches_exist():
    init_db()
    db = SessionLocal()
    try:
        matches = []
        for i in range(6):
            matches.append(
                {
                    "external_id": f"api-test-{i}",
                    "competition": "Test League",
                    "played_at": datetime.fromisoformat(f"2024-01-{i + 1:02d}T00:00:00"),
                    "home_team": "Alpha FC",
                    "away_team": "Beta United",
                    "home_goals": 2,
                    "away_goals": 1,
                }
            )
        import_matches(db, matches)
    finally:
        db.close()

    response = client.get("/predict", params={"home": "Alpha FC", "away": "Beta United"})
    assert response.status_code == 200
    body = response.json()
    assert body["reliable"] is True
    assert 0.0 <= body["home_win"] <= 1.0
    assert len(body["top_scores"]) == 3
