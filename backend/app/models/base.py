from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

SCHEMA_NAME = "cinematch"


class Base(DeclarativeBase):
    """Declarative Base scoped to the cinematch PostgreSQL schema."""

    metadata = MetaData(schema=SCHEMA_NAME)
