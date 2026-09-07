from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...analytics.model_variants import MODEL_NAMES
from ...ml.artifact import load_artifact
from ...models.enums import Confidence, Continent
from ...services.backtest_service import BacktestFilters, backtest_compare
from ..deps import get_db

router = APIRouter(prefix="/backtesting", tags=["backtesting"])


@router.get("")
def backtesting(
    competition_id: int | None = None,
    country_id: int | None = None,
    continent: Continent | None = None,
    season_id: int | None = None,
    min_confidence: Confidence | None = None,
    db: Session = Depends(get_db),
) -> dict:
    filters = BacktestFilters(
        competition_id=competition_id,
        country_id=country_id,
        continent=continent,
        season_id=season_id,
        min_confidence=min_confidence.value if min_confidence else None,
    )
    artifact = load_artifact()
    models = list(MODEL_NAMES) + (["ml"] if artifact else [])
    return backtest_compare(db, models, filters)
