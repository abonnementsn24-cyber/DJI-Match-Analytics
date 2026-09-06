from app.core.config import get_settings
from app.jobs import scheduler as scheduler_module


def test_scheduler_disabled_by_default_in_tests():
    # tests/conftest.py sets ENABLE_SCHEDULER=false before the app is
    # imported, so pytest never leaves background threads running.
    assert get_settings().enable_scheduler is False
    assert scheduler_module.start_scheduler() is None


def test_scheduler_starts_and_registers_all_jobs_when_enabled(monkeypatch):
    monkeypatch.setattr(get_settings(), "enable_scheduler", True, raising=False)
    scheduler_module._scheduler = None
    try:
        sched = scheduler_module.start_scheduler()
        assert sched is not None
        assert sched.running is True
        assert {job.id for job in sched.get_jobs()} == {
            "discover",
            "sync-popular-leagues",
            "evaluate",
            "metrics-snapshot",
        }
    finally:
        scheduler_module.stop_scheduler()


def test_start_scheduler_is_idempotent(monkeypatch):
    monkeypatch.setattr(get_settings(), "enable_scheduler", True, raising=False)
    scheduler_module._scheduler = None
    try:
        first = scheduler_module.start_scheduler()
        second = scheduler_module.start_scheduler()
        assert first is second
    finally:
        scheduler_module.stop_scheduler()


def test_scheduler_jobs_do_not_crash_in_demo_mode(db):
    # demo_mode is True in the test settings (no FOOTBALL_DATA_API_KEY), so
    # the discover/sync jobs must no-op cleanly rather than raise.
    scheduler_module._job_discover()
    scheduler_module._job_sync_popular_leagues()
    scheduler_module._job_evaluate()
    scheduler_module._job_metrics_snapshot()
