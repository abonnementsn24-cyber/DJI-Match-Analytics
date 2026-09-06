import datetime

from app.analytics.elo import EloState
from app.analytics.model_variants import MatchContext
from app.analytics.team_state import LeagueState
from app.ml.artifact import load_artifact
from app.ml.predict import make_predict_fn
from app.ml.train import MIN_TRAINING_SAMPLES, train_model

from .helpers import seed_league


def test_train_model_refuses_when_not_enough_samples(db):
    seed_league(db, n_teams=3, n_rounds=1)  # far fewer than MIN_TRAINING_SAMPLES

    result = train_model(db)

    assert result["trained"] is False
    assert str(MIN_TRAINING_SAMPLES) in result["reason"]
    assert load_artifact() is None


def test_train_model_succeeds_with_enough_history_and_uses_chronological_split(db):
    seed_league(db, n_teams=8, n_rounds=6)  # 8*7*6 = 336 matches, well above MIN_TRAINING_SAMPLES

    result = train_model(db)

    assert result["trained"] is True
    assert result["train_samples"] + result["val_samples"] + result["test_samples"] > MIN_TRAINING_SAMPLES
    # Chronological split: train/val/test roughly 70/15/15
    assert result["train_samples"] > result["val_samples"]
    assert result["train_samples"] > result["test_samples"]
    assert result["test_report"]["matches"] == result["test_samples"]

    artifact = load_artifact()
    assert artifact is not None
    assert artifact["algorithm"] == "hist_gradient_boosting"


def test_make_predict_fn_returns_normalized_probabilities(db):
    seed_league(db, n_teams=8, n_rounds=6)
    train_model(db)
    artifact = load_artifact()

    predict_fn = make_predict_fn(artifact)
    state, elo = LeagueState(), EloState()
    ctx = MatchContext(home_team_id=1, away_team_id=2)

    result = predict_fn(state, elo, ctx, datetime.datetime(2025, 1, 1))
    assert result is not None
    home_p, draw_p, away_p, exp_home, exp_away = result
    assert abs((home_p + draw_p + away_p) - 1.0) < 1e-6
    assert exp_home > 0
    assert exp_away > 0
