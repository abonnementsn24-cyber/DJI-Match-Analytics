from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...analytics.model_variants import MODEL_NAMES
from ...ml.artifact import load_artifact
from ...services.backtest_service import (
    BacktestFilters,
    backtest_model,
    monthly_breakdown,
)
from ..deps import get_db

router = APIRouter(prefix="/models", tags=["models"])

_DESCRIPTIONS = {
    "basic": {
        "label": "Poisson Basic",
        "variables": ["buts marqués/encaissés (historique complet, domicile/extérieur)"],
    },
    "form": {
        "label": "Poisson Form",
        "variables": ["forme récente (10 derniers matchs, domicile/extérieur séparés)"],
    },
    "elo": {
        "label": "Elo Model",
        "variables": ["rating Elo chronologique", "avantage du terrain"],
    },
    "ensemble": {
        "label": "Ensemble",
        "variables": ["Poisson Basic", "Poisson Form", "Elo", "H2H", "repos"],
    },
    "ml": {
        "label": "Machine Learning",
        "variables": ["écart Elo", "forme domicile/extérieur", "H2H", "repos (classification HOME/DRAW/AWAY)"],
    },
}


@router.get("")
def list_models(db: Session = Depends(get_db)) -> list[dict]:
    artifact = load_artifact()
    names = list(MODEL_NAMES) + (["ml"] if artifact else [])

    out = []
    for name in names:
        report = backtest_model(db, name)
        entry = {
            "name": name,
            **_DESCRIPTIONS.get(name, {}),
            "matches_evaluated": report.matches_evaluated,
            "accuracy": report.as_dict()["accuracy"],
            "brier_score": report.as_dict()["brier_score"],
            "log_loss": report.as_dict()["log_loss"],
        }
        if name == "ml" and artifact:
            entry["version"] = artifact.get("version")
            entry["trained_at"] = artifact.get("trained_at")
            entry["algorithm"] = artifact.get("algorithm")
            entry["test_report"] = artifact.get("test_report")
        out.append(entry)
    return out


@router.get("/metrics")
def models_metrics(
    model: str | None = None,
    competition_id: int | None = None,
    db: Session = Depends(get_db),
) -> dict:
    artifact = load_artifact()
    names = [model] if model else list(MODEL_NAMES) + (["ml"] if artifact else [])
    filters = BacktestFilters(competition_id=competition_id)

    return {
        name: {
            "summary": backtest_model(db, name, filters).as_dict(),
            "monthly": monthly_breakdown(db, name, filters),
        }
        for name in names
    }
