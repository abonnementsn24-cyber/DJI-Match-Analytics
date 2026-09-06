"""Points the app at a throwaway SQLite file before any test module (or the
app itself) is imported, so tests never touch a developer's real database.
"""
import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db')}"
os.environ.setdefault("ML_ARTIFACT_DIR", tempfile.mkdtemp())

import pytest

from app import models  # noqa: F401  (registers all ORM models on Base.metadata)
from app.db.base import Base
from app.db.session import SessionLocal, engine, init_db


@pytest.fixture()
def db():
    """A clean schema for every test: no leftover rows from a previous test
    can leak into (or be mistaken for) another test's data."""
    Base.metadata.drop_all(bind=engine)
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
