"""Points the app at a throwaway SQLite file before any test module (or the
app itself) is imported, so tests never touch a developer's real database.
"""
import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db')}"
