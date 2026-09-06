from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .backtest import run_backtest, run_backtest_compare
from .connectors.football_data import FootballDataError, fetch_finished_matches
from .database import get_db, init_db
from .history import build_state
from .importer import import_matches
from .models import Team
from .predictor import DEFAULT_MODEL, predict
from .standings import compute_standings
from .variants import MODEL_NAMES


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
    version="0.2.0",
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


@app.get("/teams/{name}/stats")
def team_stats_endpoint(name: str, db: Session = Depends(get_db)) -> dict:
    _, stats = build_state(db)
    record = stats.get(name)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Équipe inconnue: {name}")
    return {"team": name, **record.as_dict()}


@app.get("/h2h")
def head_to_head_endpoint(
    team_a: str = Query(...), team_b: str = Query(...), db: Session = Depends(get_db)
) -> dict:
    _, stats = build_state(db)
    meetings = stats.head_to_head(team_a, team_b)
    wins_a = sum(1 for h, a, hg, ag in meetings if (h == team_a and hg > ag) or (a == team_a and ag > hg))
    wins_b = sum(1 for h, a, hg, ag in meetings if (h == team_b and hg > ag) or (a == team_b and ag > hg))
    draws = len(meetings) - wins_a - wins_b
    return {
        "team_a": team_a,
        "team_b": team_b,
        "matches_played": len(meetings),
        "wins_a": wins_a,
        "wins_b": wins_b,
        "draws": draws,
        "meetings": [
            {"home_team": h, "away_team": a, "home_goals": hg, "away_goals": ag}
            for h, a, hg, ag in meetings
        ],
    }


@app.get("/standings")
def standings_endpoint(
    competition: str | None = Query(None), db: Session = Depends(get_db)
) -> list[dict]:
    return compute_standings(db, competition)


@app.get("/predict")
def predict_match_endpoint(
    home: str = Query(..., description="Nom de l'équipe à domicile"),
    away: str = Query(..., description="Nom de l'équipe à l'extérieur"),
    model: str = Query(DEFAULT_MODEL, description=f"Modèle à utiliser: {MODEL_NAMES}"),
    db: Session = Depends(get_db),
) -> dict:
    ratings, stats = build_state(db)
    try:
        result = predict(ratings, stats, home, away, model=model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.as_dict()


@app.get("/predict/compare")
def predict_compare_endpoint(
    home: str = Query(...), away: str = Query(...), db: Session = Depends(get_db)
) -> dict:
    ratings, stats = build_state(db)
    return {
        model: predict(ratings, stats, home, away, model=model).as_dict() for model in MODEL_NAMES
    }


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
def backtest_endpoint(
    model: str = Query(DEFAULT_MODEL, description=f"Modèle à évaluer: {MODEL_NAMES}"),
    db: Session = Depends(get_db),
) -> dict:
    try:
        report = run_backtest(db, model=model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return report.as_dict()


@app.get("/backtest/compare")
def backtest_compare_endpoint(db: Session = Depends(get_db)) -> dict:
    return run_backtest_compare(db)
