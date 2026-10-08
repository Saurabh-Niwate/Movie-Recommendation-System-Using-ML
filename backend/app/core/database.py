import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

# Synchronous SQLAlchemy 2.0 engine using psycopg 3 driver
engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_timeout=settings.pool_timeout,
    pool_recycle=settings.pool_recycle,
    pool_pre_ping=settings.pool_pre_ping,
    echo=settings.echo_sql,
    connect_args={
        "options": f"-csearch_path={settings.db_schema},public"
    },
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a synchronous SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_exists(bind=None) -> None:
    """Ensure the target PostgreSQL schema exists before running operations."""
    target_engine = bind if bind is not None else engine
    with target_engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema}"))
        conn.commit()
    logger.info("Ensured database schema '%s' exists", settings.db_schema)

