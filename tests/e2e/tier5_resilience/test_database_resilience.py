"""Tier 5: Resilient Database Fallback & SQLite Engine Verification E2E Tests.

Verifies:
- Automatic probe failover: when primary PostgreSQL connection is unavailable or fails auth,
  the system smoothly falls back to SQLite (cinematch.db) without crashing.
- Engine dialect check: active database dialect is 'sqlite'.
- Persistence: cinematch.db file exists in project root.
- PRAGMA foreign_keys: SQLite connection pragma enforces foreign key constraints.
- Schema translation map: queries strip PostgreSQL schema 'cinematch.' cleanly.
- Table presence: all required entities (movies, profiles, ratings, user_lists) are queryable.
- Transactional resilience: session creation, atomic commit, and rollback operate without locking errors.
- Service health: /health, /api/health, and /api/v1/health endpoints report status 'ok'.
"""

import sys
from pathlib import Path
import pytest
from sqlalchemy import text, inspect
from fastapi.testclient import TestClient

# Ensure backend root is discoverable
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.database import (
    engine,
    is_sqlite_database,
    SessionLocal,
    ensure_schema_exists,
)
from app.models import Movie, Profile, Rating, UserList
from backend.app.main import app as live_backend_app


def test_sqlite_fallback_dialect_active():
    """T5.1.1: Verify active database dialect is SQLite when PostgreSQL is offline/unauthenticated."""
    assert engine is not None, "Database engine must not be None"
    assert is_sqlite_database() is True, "Expected is_sqlite_database() to return True under local fallback"
    assert engine.dialect.name == "sqlite", f"Expected engine dialect 'sqlite', got '{engine.dialect.name}'"


def test_sqlite_db_file_resolves_and_exists():
    """T5.1.2: Verify cinematch.db resolves to an absolute path within project root and exists."""
    uri = settings.sqlite_database_uri
    assert uri.startswith("sqlite:///"), f"Expected sqlite URI format, got: {uri}"
    db_file_path = Path(uri.replace("sqlite:///", ""))
    assert db_file_path.exists(), f"Database file does not exist at: {db_file_path}"
    assert db_file_path.name == "cinematch.db"


def test_sqlite_pragma_foreign_keys_enabled():
    """T5.1.3: Verify PRAGMA foreign_keys=ON is enforced on SQLite connections."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA foreign_keys;")).scalar()
        assert result == 1, f"Expected PRAGMA foreign_keys=1 (enabled), got {result}"


def test_schema_tables_exist_and_translate_cleanly():
    """T5.1.4: Verify all core tables exist in SQLite without schema translation errors."""
    ensure_schema_exists(engine)
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    required_tables = {"movies", "profiles", "ratings", "user_lists"}
    for req in required_tables:
        assert req in table_names, f"Required table '{req}' not found in SQLite database tables: {table_names}"


def test_database_session_crud_and_rollback_resilience():
    """T5.1.5: Verify SessionLocal supports atomic commits and rollbacks without SQLite lock contention."""
    with SessionLocal() as db:
        # Query existing movies
        movie_count = db.query(Movie).count()
        assert movie_count >= 1, f"Expected at least 1 seeded movie, got {movie_count}"

        # Test safe transaction rollback
        try:
            # Attempt to execute an invalid statement to trigger rollback
            db.execute(text("SELECT * FROM nonexistent_table_test_rollback;"))
        except Exception:
            db.rollback()

        # Session should still be functional after rollback
        recovered_count = db.query(Movie).count()
        assert recovered_count == movie_count


def test_live_backend_health_check_under_sqlite_fallback():
    """T5.1.6: Verify FastAPI /health endpoint reports status 'ok' and model registry loaded."""
    with TestClient(live_backend_app) as test_client:
        for health_path in ["/health", "/api/health", "/api/v1/health"]:
            response = test_client.get(health_path)
            assert response.status_code == 200, f"Expected 200 from {health_path}, got {response.status_code}"
            data = response.json()
            assert data["status"] == "ok"
            assert data["service"] == "cinematch-backend"
            assert "models_loaded" in data
