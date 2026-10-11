from pathlib import Path
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_env_file() -> Optional[str]:
    """Search for .env starting from cwd up through parent directories."""
    # Check cwd
    cwd_env = Path.cwd() / ".env"
    if cwd_env.is_file():
        return str(cwd_env)

    # Check relative to this file (backend/app/core/config.py -> 3 parents up is root)
    current = Path(__file__).resolve()
    for parent in current.parents:
        cand = parent / ".env"
        if cand.is_file():
            return str(cand)

    return None


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database Configuration
    db_name: str = "postgres"
    db_user: str = "user2"
    db_password: str = "123"
    db_host: str = "localhost"
    db_port: int = 5432
    db_schema: str = "cinematch"

    # Database Fallback Configuration
    sqlite_db_path: str = "cinematch.db"
    db_fallback_sqlite: bool = True
    db_connect_timeout: int = 3
    database_url: Optional[str] = None

    # Connection Pool Settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800
    pool_pre_ping: bool = True
    echo_sql: bool = False

    # External APIs
    tmdb_api: str = "apikey"
    tmdb_read_token: Optional[str] = None
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_image_base_url: str = "https://image.tmdb.org/t/p"

    # JWT Authentication Configuration
    jwt_secret_key: str = "cinematch-secret-token-key-2026-production-ready"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Application Settings
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    def __init__(self, **values: object) -> None:
        super().__init__(**values)
        if "tmdb_api" in values and "tmdb_read_token" not in values:
            self.tmdb_read_token = str(values["tmdb_api"]).strip()

    @property
    def jwt_secret(self) -> str:
        return self.jwt_secret_key

    @field_validator("db_port", mode="before")
    @classmethod
    def strip_and_parse_port(cls, v: object) -> int:
        """Strip any whitespace from DB_PORT (e.g. '5432 ') before parsing integer."""
        if isinstance(v, str):
            v_cleaned = v.strip()
            return int(v_cleaned)
        if isinstance(v, int):
            return v
        raise ValueError(f"Invalid port value: {v}")

    @field_validator("db_user", "db_name", "db_host", "db_password", "db_schema", "tmdb_api", "sqlite_db_path", mode="before")
    @classmethod
    def strip_whitespace_strings(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @property
    def sqlite_database_uri(self) -> str:
        """Construct synchronous SQLite connection string resolving absolute path in project root."""
        path = Path(self.sqlite_db_path)
        if not path.is_absolute():
            current = Path(__file__).resolve()
            root = None
            for p in current.parents:
                if (p / "PROJECT.md").is_file() or (p / ".git").exists():
                    root = p
                    break
            if root is None:
                root = current.parents[3] if len(current.parents) >= 4 else Path.cwd()
            path = (root / path).resolve()
        return f"sqlite:///{path.as_posix()}"

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Construct synchronous psycopg connection string or override."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def effective_tmdb_read_token(self) -> Optional[str]:
        """Return clean TMDB API Read Access Token, falling back to tmdb_api if provided."""
        token = self.tmdb_read_token or self.tmdb_api
        if not token:
            return None
        cleaned = token.strip()
        if cleaned.lower() in {"", "apikey", "dummy", "placeholder", "test", "none"}:
            return None
        return cleaned

    @property
    def is_tmdb_mock_enabled(self) -> bool:
        """Return True if TMDB API read key is missing, placeholder, or offline."""
        return self.effective_tmdb_read_token is None


settings = Settings()
