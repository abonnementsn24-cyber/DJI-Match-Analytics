from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import joblib

ARTIFACT_DIR = Path(os.environ.get("ML_ARTIFACT_DIR", Path(__file__).parent / "artifacts"))
ARTIFACT_PATH = ARTIFACT_DIR / "outcome_classifier.joblib"

MODEL_NAME = "ml"
MODEL_VERSION = "1.0.0"


def save_artifact(payload: dict[str, Any]) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, ARTIFACT_PATH)
    return ARTIFACT_PATH


def load_artifact() -> dict[str, Any] | None:
    if not ARTIFACT_PATH.exists():
        return None
    return joblib.load(ARTIFACT_PATH)
