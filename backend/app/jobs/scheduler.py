"""Automatic updates (§19 of the brief): morning discovery, periodic sync
of the popular leagues, post-match evaluation, and a nightly metrics
snapshot — so the platform keeps itself current without a human running
the CLI by hand.

Uses APScheduler's ``BackgroundScheduler`` (a plain thread pool) since
every job below is synchronous, blocking SQLAlchemy work — no need for an
async scheduler alongside FastAPI's own event loop. Each job opens its own
DB session and never lets an exception escape (a crashed job just logs and
waits for its next tick instead of taking the scheduler down).

Disabled during tests (``ENABLE_SCHEDULER=false``, set in
tests/conftest.py) so pytest never starts background threads that outlive
the test process.
"""
from __future__ import annotations

import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from ..analytics.model_variants import MODEL_NAMES
from ..core.config import get_settings
from ..core.logging import get_logger
from ..db.session import SessionLocal
from ..ml.artifact import load_artifact
from ..providers.base import ProviderError
from ..providers.registry import get_provider
from ..services.backtest_service import persist_metrics_snapshot
from ..services.discovery_service import discover_competitions
from ..services.evaluation_service import evaluate_finished_predictions
from ..services.prediction_service import generate_all_predictions
from ..services.sync_service import sync_popular_leagues

logger = get_logger(__name__)

_scheduler: BackgroundScheduler | None = None


def _job_discover() -> None:
    if get_settings().demo_mode:
        logger.info("Scheduler: mode démo actif, découverte automatique ignorée (aucune clé API).")
        return
    db = SessionLocal()
    try:
        report = discover_competitions(db, get_provider())
        logger.info("Scheduler discover: %s", report.as_dict())
    except ProviderError as exc:
        logger.warning("Scheduler discover job failed: %s", exc)
    except Exception:
        logger.exception("Scheduler discover job crashed")
    finally:
        db.close()


def _job_sync_popular_leagues() -> None:
    if get_settings().demo_mode:
        logger.info("Scheduler: mode démo actif, synchronisation automatique ignorée (aucune clé API).")
        return
    db = SessionLocal()
    try:
        results = sync_popular_leagues(db, get_provider())
        logger.info("Scheduler sync-popular: %s", {code: r.get("ok") for code, r in results.items()})
        generate_all_predictions(db)
        evaluate_finished_predictions(db)
    except Exception:
        logger.exception("Scheduler sync-popular job crashed")
    finally:
        db.close()


def _job_evaluate() -> None:
    db = SessionLocal()
    try:
        count = evaluate_finished_predictions(db)
        if count:
            logger.info("Scheduler evaluate: %d prédictions évaluées.", count)
    except Exception:
        logger.exception("Scheduler evaluate job crashed")
    finally:
        db.close()


def _job_metrics_snapshot() -> None:
    db = SessionLocal()
    try:
        models = list(MODEL_NAMES) + (["ml"] if load_artifact() else [])
        written = persist_metrics_snapshot(db, models)
        logger.info("Scheduler metrics-snapshot: %d modèles enregistrés.", written)
    except Exception:
        logger.exception("Scheduler metrics-snapshot job crashed")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler | None:
    """Idempotent: a second call (e.g. an extra reload worker) returns the
    already-running instance instead of starting a duplicate."""
    global _scheduler
    settings = get_settings()

    if not settings.enable_scheduler:
        logger.info("Scheduler désactivé (ENABLE_SCHEDULER=false).")
        return None
    if _scheduler is not None:
        return _scheduler

    now = datetime.datetime.now(datetime.timezone.utc)
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _job_discover, "interval", hours=settings.discover_interval_hours, id="discover", next_run_time=now
    )
    scheduler.add_job(
        _job_sync_popular_leagues,
        "interval",
        hours=settings.sync_popular_leagues_interval_hours,
        id="sync-popular-leagues",
        next_run_time=now,
    )
    scheduler.add_job(
        _job_evaluate, "interval", minutes=settings.evaluate_interval_minutes, id="evaluate"
    )
    scheduler.add_job(
        _job_metrics_snapshot,
        "interval",
        hours=settings.metrics_snapshot_interval_hours,
        id="metrics-snapshot",
    )
    scheduler.start()
    _scheduler = scheduler

    logger.info(
        "Scheduler démarré (discover=%dh, sync-popular=%dh, evaluate=%dmin, metrics=%dh)",
        settings.discover_interval_hours,
        settings.sync_popular_leagues_interval_hours,
        settings.evaluate_interval_minutes,
        settings.metrics_snapshot_interval_hours,
    )
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
