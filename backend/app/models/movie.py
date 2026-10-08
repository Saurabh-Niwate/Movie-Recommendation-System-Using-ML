from datetime import datetime
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import (
    Integer,
    String,
    Text,
    Float,
    DateTime,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.rating import Rating
    from app.models.user_list import UserList


class Movie(Base):
    """Movie catalog entity replicating MovieLens 1M enriched with TMDB metadata."""

    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movie_lens_id: Mapped[Optional[int]] = mapped_column(
        Integer, unique=True, index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title_raw: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    genres: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    # Descriptive metadata
    synopsis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    poster_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    backdrop_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tmdb_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    # Machine learning contiguous item index (0..N-1)
    item_idx: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    # Additional metadata
    vote_average: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vote_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    director: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cast: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    runtime: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    ratings: Mapped[List["Rating"]] = relationship(
        "Rating",
        back_populates="movie",
        cascade="all, delete-orphan",
    )
    user_lists: Mapped[List["UserList"]] = relationship(
        "UserList",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    @property
    def movie_id(self) -> int:
        """Alias for compatibility with services referring to movie_id."""
        return self.id

    def effective_synopsis(self) -> str:
        """Return synopsis or overview, whichever is populated."""
        return self.synopsis or self.overview or ""

    def __repr__(self) -> str:
        return f"<Movie(id={self.id}, title='{self.title}', year={self.year})>"
