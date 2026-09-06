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


def test_predict_rejects_unknown_model():
    response = client.get(
        "/predict", params={"home": "Alpha FC", "away": "Beta United", "model": "nope"}
    )
    assert response.status_code == 400


def test_predict_compare_returns_all_models():
    response = client.get("/predict/compare", params={"home": "Alpha FC", "away": "Beta United"})
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"simple", "form", "combined"}
    for prediction in body.values():
        assert prediction["reliable"] is True


def test_team_stats_endpoint():
    response = client.get("/teams/Alpha FC/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["team"] == "Alpha FC"
    assert body["home"]["matches"] == 6


def test_team_stats_endpoint_404_for_unknown_team():
    response = client.get("/teams/Nobody At All/stats")
    assert response.status_code == 404


def test_h2h_endpoint():
    response = client.get("/h2h", params={"team_a": "Alpha FC", "team_b": "Beta United"})
    assert response.status_code == 200
    body = response.json()
    assert body["matches_played"] == 6
    assert body["wins_a"] == 6


def test_standings_endpoint():
    response = client.get("/standings", params={"competition": "Test League"})
    assert response.status_code == 200
    body = response.json()
    assert body[0]["team"] == "Alpha FC"


def test_backtest_compare_endpoint():
    response = client.get("/backtest/compare")
    assert response.status_code == 200
    body = response.json()
    assert set(body["models"].keys()) == {"simple", "form", "combined"}
