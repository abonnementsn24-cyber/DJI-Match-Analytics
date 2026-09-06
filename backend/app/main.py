from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.v1.router import api_router
from .core.config import get_settings
from .core.logging import configure_logging, get_logger
from .db.session import init_db
from .jobs.scheduler import start_scheduler, stop_scheduler
from .providers.base import ProviderError

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="EMDJI Match Analytics",
    description=(
        "Football Intelligence & Predictive Analytics — plateforme d'analyse statistique "
        "de matchs de football. Probabilités 1/N/2, buts attendus, BTTS et scores les plus "
        "probables, calculés par 5 modèles comparables (Poisson Basic/Form, Elo, Ensemble, ML) "
        "et mesurés objectivement par backtesting chronologique. Aucune fonctionnalité de pari, "
        "aucune connexion à un bookmaker, aucune recommandation financière."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(ProviderError)
async def provider_error_handler(_: Request, exc: ProviderError) -> JSONResponse:
    logger.warning("Provider error: %s", exc)
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erreur interne non gérée")
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne est survenue. Merci de réessayer plus tard."},
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "demo_mode": get_settings().demo_mode}
