from app.models.competition import Competition
from app.services.popular_leagues import POPULAR_LEAGUES, UNAVAILABLE_FROM_PROVIDER, popular_league_codes
from app.services.sync_service import sync_popular_leagues

from .fakes import FakeProvider


def test_popular_league_codes_are_unique_and_nonempty():
    codes = popular_league_codes()
    assert len(codes) == len(POPULAR_LEAGUES) > 0
    assert len(set(codes)) == len(codes)


def test_saudi_arabia_is_documented_as_unavailable():
    reasons = " ".join(u["requested"] for u in UNAVAILABLE_FROM_PROVIDER)
    assert "Saudi" in reasons or "Saoudite" in reasons


def test_sync_popular_leagues_runs_discovery_and_reports_per_league(db):
    provider = FakeProvider()
    # None of FakeProvider's competitions use a popular-league code, so every
    # entry should come back as "not found" rather than crash the batch.
    results = sync_popular_leagues(db, provider, codes=["PL", "PD"])

    assert set(results.keys()) == {"PL", "PD"}
    for result in results.values():
        assert result["ok"] is False


def test_sync_popular_leagues_syncs_a_matching_code(db):
    provider = FakeProvider()
    provider.competitions[0].code = "PL"  # pretend the fake league is "PL"

    results = sync_popular_leagues(db, provider, codes=["PL"])

    assert results["PL"]["ok"] is True
    assert results["PL"]["matches_added"] == 1
    assert db.query(Competition).filter(Competition.code == "PL").count() == 1
