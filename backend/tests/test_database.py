import pytest
from sqlalchemy import text
from app.core.database import engine, SessionLocal, get_db
from app.core.config import settings


def test_database_connection():
    """Verify live synchronous database connection and search_path."""
    with engine.connect() as conn:
        search_path = conn.execute(text("SHOW search_path;")).scalar()
        assert "cinematch" in search_path

        version = conn.execute(text("SELECT version();")).scalar()
        assert "PostgreSQL" in version


def test_session_generator():
    """Verify get_db dependency yields active session and closes cleanly."""
    gen = get_db()
    session = next(gen)
    assert session.is_active

    result = session.execute(text("SELECT 1;")).scalar()
    assert result == 1

    with pytest.raises(StopIteration):
        next(gen)
