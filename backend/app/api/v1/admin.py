from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...ml.train import train_model
from ...providers.base import ProviderError
from ...providers.registry import get_provider
from ...services.discovery_service import discover_competitions
from ...services.evaluation_service import evaluate_finished_predictions
from ...services.prediction_service import (
    generate_all_predictions,
    generate_predictions_for_competition,
)
from ...services.sync_service import sync_competition, sync_popular_leagues
from ..deps import get_db, require_admin_token

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_token)])


@router.post("/discover")
def admin_discover(provider_name: str = Query("football-data"), db: Session = Depends(get_db)) -> dict:
    try:
        provider = get_provider(provider_name)
        report = discover_competitions(db, provider)
        return report.as_dict()
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/sync")
def admin_sync(
    code: str,
    season: int | None = None,
    provider_name: str = Query("football-data"),
    db: Session = Depends(get_db),
) -> dict:
    if get_settings().demo_mode:
        raise HTTPException(
            status_code=409,
            detail=(
                "Aucune clé FOOTBALL_DATA_API_KEY configurée — l'application tourne en "
                "mode démo. Configurez la clé pour synchroniser des données réelles."
            ),
        )
    try:
        provider = get_provider(provider_name)
        report = sync_competition(db, provider, code, season_year=season)
        return report.as_dict()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sync-popular")
def admin_sync_popular(provider_name: str = Query("football-data"), db: Session = Depends(get_db)) -> dict:
    if get_settings().demo_mode:
        raise HTTPException(
            status_code=409,
            detail=(
                "Aucune clé FOOTBALL_DATA_API_KEY configurée — l'application tourne en "
                "mode démo. Configurez la clé pour synchroniser des données réelles."
            ),
        )
    provider = get_provider(provider_name)
    return sync_popular_leagues(db, provider)


@router.post("/generate-predictions")
def admin_generate_predictions(competition_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    if competition_id is not None:
        return generate_predictions_for_competition(db, competition_id)
    return generate_all_predictions(db)


@router.post("/evaluate")
def admin_evaluate(db: Session = Depends(get_db)) -> dict:
    count = evaluate_finished_predictions(db)
    return {"predictions_evaluated": count}


@router.post("/train-ml")
def admin_train_ml(algorithm: str = Query("hist_gradient_boosting"), db: Session = Depends(get_db)) -> dict:
    return train_model(db, algorithm=algorithm)
