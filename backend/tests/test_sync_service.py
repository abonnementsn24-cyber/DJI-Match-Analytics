import pytest

from app.models.match import Match
from app.models.team import Team
from app.services.discovery_service import discover_competitions
from app.services.sync_service import sync_competition

from .fakes import FakeProvider


def test_sync_competition_pulls_seasons_teams_and_matches(db):
    provider = FakeProvider()
    discover_competitions(db, provider)

    report = sync_competition(db, provider, code="FL")

    assert report.errors == []
    assert report.seasons_synced == 1
    assert report.teams_synced == 2
    assert report.matches_added == 1
    assert db.query(Team).count() == 2
    assert db.query(Match).count() == 1


def test_sync_competition_is_idempotent(db):
    provider = FakeProvider()
    discover_competitions(db, provider)
    sync_competition(db, provider, code="FL")
    report = sync_competition(db, provider, code="FL")

    # Re-running finds the same season/teams/match already there.
    assert report.matches_added == 0
    assert report.matches_updated == 1
    assert db.query(Match).count() == 1


def test_sync_unknown_competition_raises(db):
    provider = FakeProvider()
    with pytest.raises(ValueError, match="inconnue"):
        sync_competition(db, provider, code="NOPE")
