"""Test setup. Integration tests need a real Postgres: set TEST_DATABASE_URL
(e.g. postgresql://user:pw@localhost:5433/chineselearn_test). They are skipped otherwise."""
import os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("APP_ENV", "test")  # disables SQL echo
TEST_DB = os.environ.get("TEST_DATABASE_URL")
if TEST_DB:
    os.environ["DATABASE_URL"] = TEST_DB  # must be set before core.config is imported
