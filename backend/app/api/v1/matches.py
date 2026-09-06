from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ...analytics.model_variants import MODEL_NAMES
from ...analytics.replay_engine import build_current_state
from ...models.competition import Competition
from ...models.enums import Continent, MatchStatus
from ...models.match import Match
from ...models.prediction import Prediction
from ...models.team import Team
from ..deps import get_db
from .serializers import serialize_match_summary, serialize_prediction

router = APIRouter(prefix="/matches", tags=["matches"])

DEFAULT_MODEL = "ensemble"


def _with_embedded_prediction(db: Session, matches: list[Match], model: str = DEFAULT_MODEL) -> list[dict]:
    match_ids = [m.id for m in matches]
    predictions = {
        p.match_id: p
        for p in db.query(Prediction)
        .filter(Prediction.match_id.in_(match_ids), Prediction.model_name == model)
        .all()
    }
    out = []
    for match in matches:
        payload = serialize_match_summary(match)
        prediction = predictions.get(match.id)
        payload["prediction"] = serialize_prediction(prediction) if prediction else None
        out.append(payload)
    return out


def _base_query(db: Session):
    return db.query(Match).options(
        joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition)
    )


def _apply_filters(
    query,
    continent: Continent | None,
    country_id: int | None,
    competition_id: int | None,
    team_id: int | None,
):
    if competition_id is not None:
        query = query.filter(Match.competition_id == competition_id)
    if team_id is not None:
        query = query.filter((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
    if continent is not None or country_id is not None:
        query = query.join(Competition, Match.competition_id == Competition.id)
        if continent is not None:
            query = query.filter(Competition.continent == continent)
        if country_id is not None:
            query = query.filter(Competition.country_id == country_id)
    return query


@router.get("/today")
def matches_today(
    model: str = Query(DEFAULT_MODEL),
    continent: Continent | None = None,
    country_id: int | None = None,
    competition_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    now = datetime.datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + datetime.timedelta(days=1)

    query = _base_query(db).filter(Match.utc_date >= start, Match.utc_date < end)
    query = _apply_filters(query, continent, country_id, competition_id, None)
    matches = query.order_by(Match.utc_date.asc()).all()
    return _with_embedded_prediction(db, matches, model)


@router.get("/upcoming")
def matches_upcoming(
    days: int = Query(7, ge=1, le=30),
    model: str = Query(DEFAULT_MODEL),
    continent: Continent | None = None,
    country_id: int | None = None,
    competition_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    now = datetime.datetime.utcnow()
    end = now + datetime.timedelta(days=days)

    query = _base_query(db).filter(
        Match.utc_date >= now,
        Match.utc_date < end,
        Match.status.in_([MatchStatus.SCHEDULED, MatchStatus.TIMED]),
    )
    query = _apply_filters(query, continent, country_id, competition_id, None)
    matches = query.order_by(Match.utc_date.asc()).all()
    return _with_embedded_prediction(db, matches, model)


@router.get("")
def list_matches(
    tab: str = Query("today", pattern="^(today|tomorrow|week|finished)$"),
    model: str = Query(DEFAULT_MODEL),
    continent: Continent | None = None,
    country_id: int | None = None,
    competition_id: int | None = None,
    team_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    """Backs the Match Center's tabs (Aujourd'hui/Demain/Cette semaine/Terminés)."""
    now = datetime.datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    query = _base_query(db)
    if tab == "today":
        query = query.filter(Match.utc_date >= today_start, Match.utc_date < today_start + datetime.timedelta(days=1))
    elif tab == "tomorrow":
        tomorrow_start = today_start + datetime.timedelta(days=1)
        query = query.filter(Match.utc_date >= tomorrow_start, Match.utc_date < tomorrow_start + datetime.timedelta(days=1))
    elif tab == "week":
        query = query.filter(Match.utc_date >= today_start, Match.utc_date < today_start + datetime.timedelta(days=7))
    else:  # finished
        query = query.filter(Match.status == MatchStatus.FINISHED)

    query = _apply_filters(query, continent, country_id, competition_id, team_id)
    total = query.count()
    order = Match.utc_date.desc() if tab == "finished" else Match.utc_date.asc()
    matches = query.order_by(order).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "results": _with_embedded_prediction(db, matches, model),
    }


@router.get("/{match_id}")
def match_detail(match_id: int, db: Session = Depends(get_db)) -> dict:
    match = _base_query(db).filter(Match.id == match_id).one_or_none()
    if match is None:
        raise HTTPException(status_code=404, detail="Match introuvable.")
    return serialize_match_summary(match)


@router.get("/{match_id}/h2h")
def match_h2h(match_id: int, db: Session = Depends(get_db)) -> dict:
    match = db.query(Match).filter(Match.id == match_id).one_or_none()
    if match is None:
        raise HTTPException(status_code=404, detail="Match introuvable.")

    state, elo = build_current_state(db)
    meetings = state.head_to_head(match.home_team_id, match.away_team_id, max_matches=5)
    team_names = {
        t.id: t.canonical_name
        for t in db.query(Team).filter(Team.id.in_({match.home_team_id, match.away_team_id})).all()
    }

    return {
        "match_id": match_id,
        "meetings": [
            {
                "home_team": team_names.get(home_id, "?"),
                "away_team": team_names.get(away_id, "?"),
                "home_goals": hg,
                "away_goals": ag,
                "date": date.isoformat(),
            }
            for home_id, away_id, hg, ag, date in meetings
        ],
        "elo": {
            "home_rating": round(elo.get(match.home_team_id), 1),
            "away_rating": round(elo.get(match.away_team_id), 1),
            "difference": round(elo.get(match.home_team_id) - elo.get(match.away_team_id), 1),
        },
    }


@router.get("/{match_id}/prediction")
def match_prediction(
    match_id: int,
    model: str = Query(DEFAULT_MODEL),
    compare: bool = Query(False, description="Renvoie les 5 modèles au lieu d'un seul"),
    db: Session = Depends(get_db),
) -> dict:
    match = db.query(Match).filter(Match.id == match_id).one_or_none()
    if match is None:
        raise HTTPException(status_code=404, detail="Match introuvable.")

    if compare:
        predictions = (
            db.query(Prediction)
            .filter(Prediction.match_id == match_id, Prediction.model_name.in_((*MODEL_NAMES, "ml")))
            .all()
        )
        if not predictions:
            return {
                "match_id": match_id,
                "reliable": False,
                "reason": "Données insuffisantes pour produire une estimation fiable.",
            }
        return {
            "match_id": match_id,
            "models": {p.model_name: serialize_prediction(p) for p in predictions},
        }

    prediction = (
        db.query(Prediction)
        .filter(Prediction.match_id == match_id, Prediction.model_name == model)
        .one_or_none()
    )
    if prediction is None:
        return {
            "match_id": match_id,
            "model": model,
            "reliable": False,
            "reason": "Données insuffisantes pour produire une estimation fiable.",
        }
    return {"match_id": match_id, "reliable": True, **serialize_prediction(prediction)}
