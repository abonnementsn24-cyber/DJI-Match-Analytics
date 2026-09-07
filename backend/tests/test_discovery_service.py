from app.models.competition import Competition
from app.models.enums import Continent
from app.services.discovery_service import discover_competitions, list_world_tree

from .fakes import FakeProvider


def test_discover_competitions_creates_competition_and_country(db):
    report = discover_competitions(db, FakeProvider())

    assert report.total_seen == 1
    assert report.newly_added == 1
    assert report.updated == 0

    competition = db.query(Competition).one()
    assert competition.canonical_name == "Fake League"
    assert competition.continent == Continent.AFRICA  # Senegal -> Africa
    assert competition.country.name == "Senegal"


def test_discover_competitions_is_idempotent(db):
    provider = FakeProvider()
    discover_competitions(db, provider)
    report = discover_competitions(db, provider)

    assert report.newly_added == 0
    assert report.updated == 1
    assert db.query(Competition).count() == 1


def test_list_world_tree_groups_by_continent_and_country(db):
    discover_competitions(db, FakeProvider())
    tree = list_world_tree(db)

    assert len(tree) == 1
    assert tree[0]["continent"] == "AFRICA"
    assert tree[0]["countries"][0]["country"] == "Senegal"
    assert tree[0]["countries"][0]["competitions"][0]["name"] == "Fake League"
