"""Thin service-layer wrapper around the replay engine, so API/CLI callers
don't need to know about ``analytics.replay_engine`` directly.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..analytics.model_variants import MODEL_NAMES
from ..analytics.replay_engine import run_full_replay
from ..ml.predict import load_latest_model, make_predict_fn


def _model_list_and_ml_fn():
    artifact = load_latest_model()
    if artifact is None:
        return MODEL_NAMES, None
    return (*MODEL_NAMES, "ml"), make_predict_fn(artifact)


def generate_predictions_for_competition(db: Session, competition_id: int) -> dict:
    models, ml_fn = _model_list_and_ml_fn()
    return run_full_replay(db, models=models, ml_predict_fn=ml_fn, competition_ids={competition_id})


def generate_all_predictions(db: Session) -> dict:
    models, ml_fn = _model_list_and_ml_fn()
    return run_full_replay(db, models=models, ml_predict_fn=ml_fn)
