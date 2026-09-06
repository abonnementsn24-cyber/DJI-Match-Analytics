from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .backtest import run_backtest
from .connectors.football_data import FootballDataError, fetch_finished_matches
from .database import get_db, init_db
from .history import build_ratings
from .importer import import_matches
from .models import Team
from .predictor import predict


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="DJI Match Analytics",
    description=(
        "Outil d'analyse statistique de matchs de football : probabilités "
        "1/N/2, buts attendus, BTTS et scores les plus probables, calculés à "
        "partir d'un modèle Poisson + Elo. Cet outil est purement analytique "
        "et ne propose ni pari ni connexion à un bookmaker."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/teams")
def list_teams(db: Session = Depends(get_db)) -> list[dict]:
    teams = db.query(Team).order_by(Team.name.asc()).all()
    return [{"name": team.name} for team in teams]


@app.get("/predict")
def predict_match_endpoint(
    home: str = Query(..., description="Nom de l'équipe à domicile"),
    away: str = Query(..., description="Nom de l'équipe à l'extérieur"),
    db: Session = Depends(get_db),
) -> dict:
    ratings = build_ratings(db)
    result = predict(ratings, home, away)
    return result.as_dict()


@app.post("/data/import/football-data")
def import_from_football_data(
    competition: str = Query(..., description="Code de compétition football-data.org, ex: PL, CL"),
    season: int | None = Query(None, description="Année de début de saison, ex: 2023"),
    db: Session = Depends(get_db),
) -> dict:
    try:
        matches = fetch_finished_matches(competition, season)
    except FootballDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    added = import_matches(db, matches)
    return {"fetched": len(matches), "added": added}


@app.get("/backtest")
def backtest_endpoint(db: Session = Depends(get_db)) -> dict:
    report = run_backtest(db)
    return report.as_dict()
