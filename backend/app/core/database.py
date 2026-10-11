import logging
from typing import Generator
from sqlalchemy import create_engine, text, event, Engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("cinematch.database")


def _probe_and_create_engine() -> Engine:
    """Attempt to connect to PostgreSQL with a short connection timeout.
    
    If PostgreSQL is unreachable or fails authentication, fall back gracefully to SQLite.
    """
    if settings.db_fallback_sqlite:
        try:
            logger.info(
                "Probing primary PostgreSQL connection (%s:%d/%s)...",
                settings.db_host,
                settings.db_port,
                settings.db_name,
            )
            pg_engine = create_engine(
                settings.sqlalchemy_database_uri,
                pool_size=settings.pool_size,
                max_overflow=settings.max_overflow,
                pool_timeout=settings.pool_timeout,
                pool_recycle=settings.pool_recycle,
                pool_pre_ping=settings.pool_pre_ping,
                echo=settings.echo_sql,
                connect_args={
                    "options": f"-csearch_path={settings.db_schema},public",
                    "connect_timeout": settings.db_connect_timeout,
                },
            )
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            logger.info("Successfully connected to primary PostgreSQL engine.")
            return pg_engine
        except Exception as exc:
            logger.warning(
                "Primary PostgreSQL connection probe failed (%s: %s). "
                "Gracefully activating SQLite fallback (%s)...",
                type(exc).__name__,
                exc,
                settings.sqlite_database_uri,
            )
    else:
        logger.info("SQLite fallback disabled; connecting to PostgreSQL directly.")
        pg_engine = create_engine(
            settings.sqlalchemy_database_uri,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
            pool_timeout=settings.pool_timeout,
            pool_recycle=settings.pool_recycle,
            pool_pre_ping=settings.pool_pre_ping,
            echo=settings.echo_sql,
            connect_args={
                "options": f"-csearch_path={settings.db_schema},public",
            },
        )
        return pg_engine

    # Fallback to SQLite
    sqlite_engine = create_engine(
        settings.sqlite_database_uri,
        connect_args={"check_same_thread": False},
        execution_options={"schema_translate_map": {settings.db_schema: None}},
        echo=settings.echo_sql,
        pool_pre_ping=settings.pool_pre_ping,
    )
    logger.info(
        "SQLite fallback engine initialized successfully: uri=%s, "
        "schema_translate_map={'%s': None}",
        settings.sqlite_database_uri,
        settings.db_schema,
    )
    return sqlite_engine


# Instantiate resilient engine at module load time
engine = _probe_and_create_engine()


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable SQLite foreign key constraints on every connection."""
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


def is_sqlite_database() -> bool:
    """Return True if the current active engine is SQLite."""
    return engine.dialect.name == "sqlite"


# Configure SessionLocal
_sessionmaker_kwargs = {
    "autocommit": False,
    "autoflush": False,
    "bind": engine,
}
if is_sqlite_database():
    _sessionmaker_kwargs["execution_options"] = {
        "schema_translate_map": {settings.db_schema: None}
    }

SessionLocal = sessionmaker(**_sessionmaker_kwargs)


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a synchronous SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_exists(bind=None) -> None:
    """Ensure target database schema exists (PostgreSQL) and all tables are created.
    
    On SQLite: skips schema creation and runs Base.metadata.create_all with schema translation.
    On PostgreSQL: creates schema if not exists, then verifies/creates tables.
    """
    target_engine = bind if bind is not None else engine

    # Import models package to register all entities (Profile, Movie, Rating, UserList) on Base.metadata
    import app.models  # noqa: F401
    from app.models.base import Base

    if target_engine.dialect.name == "sqlite":
        logger.info("SQLite engine detected; creating tables with schema_translate_map...")
        Base.metadata.create_all(bind=target_engine)
        logger.info("All CineMatch tables created/verified on SQLite.")
        return

    # PostgreSQL: ensure schema exists, then create tables if not present
    with target_engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema}"))
        conn.commit()
    logger.info("Ensured database schema '%s' exists", settings.db_schema)
    Base.metadata.create_all(bind=target_engine)
    logger.info("All CineMatch tables created/verified on PostgreSQL schema '%s'.", settings.db_schema)

