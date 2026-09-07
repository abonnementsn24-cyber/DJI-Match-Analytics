
from fastapi.testclient import TestClient

from app.analytics.replay_engine import run_full_replay
from app.main import app
from app.services.evaluation_service import evaluate_finished_predictions

from .helpers import seed_league

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_system_status_reports_demo_mode_by_default(db):
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    body = response.json()
    assert body["demo_mode"] is True
    assert body["provider_configured"] is False


def test_competitions_tree_empty_when_nothing_discovered(db):
    response = client.get("/api/v1/competitions")
    assert response.status_code == 200
    assert response.json() == []


def test_matches_today_and_prediction_flow(db):
    seed_league(db, n_teams=6, n_rounds=4)
    run_full_replay(db)
    evaluate_finished_predictions(db)

    response = client.get("/api/v1/matches", params={"tab": "finished", "page_size": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 0
    match_id = body["results"][0]["id"]

    prediction_response = client.get(f"/api/v1/matches/{match_id}/prediction")
    assert prediction_response.status_code == 200
    prediction = prediction_response.json()
    assert prediction["reliable"] is True
    assert 0.0 <= prediction["home_win_probability"] <= 1.0
    assert len(prediction["top_scores"]) == 5

    compare_response = client.get(f"/api/v1/matches/{match_id}/prediction", params={"compare": True})
    assert compare_response.status_code == 200
    assert set(compare_response.json()["models"].keys()) == {"basic", "form", "elo", "ensemble"}


def test_prediction_reports_insufficient_data_for_new_teams(db):
    seed_league(db, n_teams=3, n_rounds=1)
    run_full_replay(db)

    response = client.get("/api/v1/matches", params={"tab": "finished", "page_size": 1})
    match_id = response.json()["results"][0]["id"]

    prediction_response = client.get(f"/api/v1/matches/{match_id}/prediction")
    body = prediction_response.json()
    assert body["reliable"] is False
    assert "insuffisantes" in body["reason"]


def test_backtesting_endpoint(db):
    seed_league(db, n_teams=6, n_rounds=4)
    run_full_replay(db)
    evaluate_finished_predictions(db)

    response = client.get("/api/v1/backtesting")
    assert response.status_code == 200
    body = response.json()
    assert body["best_model"] in {"basic", "form", "elo", "ensemble"}


def test_admin_endpoints_are_open_without_token_configured(db, monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    response = client.post("/api/v1/admin/evaluate")
    assert response.status_code == 200


def test_admin_endpoints_require_bearer_token_when_configured(db, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("ADMIN_API_TOKEN", "secret123")
    get_settings.cache_clear()
    try:
        no_token = client.post("/api/v1/admin/evaluate")
        assert no_token.status_code == 401

        with_token = client.post(
            "/api/v1/admin/evaluate", headers={"Authorization": "Bearer secret123"}
        )
        assert with_token.status_code == 200
    finally:
        monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)
        get_settings.cache_clear()


def test_admin_sync_refuses_in_demo_mode(db):
    response = client.post("/api/v1/admin/sync", params={"code": "PL"})
    assert response.status_code == 409
