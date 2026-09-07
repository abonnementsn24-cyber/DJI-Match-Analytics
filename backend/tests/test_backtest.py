from app.analytics.replay_engine import run_full_replay
from app.services.backtest_service import (
    BacktestFilters,
    backtest_compare,
    backtest_model,
)
from app.services.evaluation_service import evaluate_finished_predictions

from .helpers import seed_league


def test_backtest_compare_reports_all_models_and_a_best_one(db):
    seed_league(db)
    run_full_replay(db)
    evaluate_finished_predictions(db)

    report = backtest_compare(db, ["basic", "form", "elo", "ensemble"])

    assert report["best_model"] in {"basic", "form", "elo", "ensemble"}
    for name in ("basic", "form", "elo", "ensemble"):
        model_report = report["models"][name]
        assert model_report["matches_evaluated"] > 0
        assert model_report["brier_score"] is not None
        assert model_report["classification"] is not None
        assert model_report["classification"]["confusion_matrix"]


def test_backtest_model_filters_by_competition(db):
    competition = seed_league(db)
    run_full_replay(db)
    evaluate_finished_predictions(db)

    scoped = backtest_model(db, "ensemble", BacktestFilters(competition_id=competition.id))
    unscoped = backtest_model(db, "ensemble")

    assert scoped.matches_evaluated == unscoped.matches_evaluated  # only one competition exists

    other = backtest_model(db, "ensemble", BacktestFilters(competition_id=competition.id + 999))
    assert other.matches_evaluated == 0
    assert other.brier_score is None
