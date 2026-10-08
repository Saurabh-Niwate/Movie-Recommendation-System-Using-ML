import pytest
from app.core.config import Settings


def test_settings_strips_port_whitespace():
    """Verify that trailing whitespace in DB_PORT is stripped and converted to integer."""
    s = Settings(
        db_port="5432 ",  # type: ignore[arg-type]
        db_name="postgres",
        db_user="user2",
        db_password="123",
        db_host="localhost",
    )
    assert s.db_port == 5432
    assert isinstance(s.db_port, int)


def test_settings_database_uri():
    """Verify synchronous psycopg database URI construction."""
    s = Settings(
        db_name="test_db",
        db_user="test_user",
        db_password="secret_password",
        db_host="db.example.com",
        db_port=5433,
    )
    uri = s.sqlalchemy_database_uri
    assert uri == "postgresql+psycopg://test_user:secret_password@db.example.com:5433/test_db"


def test_tmdb_mock_detection():
    """Verify TMDB mock status for placeholder keys."""
    assert Settings(tmdb_api="apikey").is_tmdb_mock_enabled is True
    assert Settings(tmdb_api="").is_tmdb_mock_enabled is True
    assert Settings(tmdb_api="dummy").is_tmdb_mock_enabled is True
    assert Settings(tmdb_api="valid_real_token_12345").is_tmdb_mock_enabled is False
