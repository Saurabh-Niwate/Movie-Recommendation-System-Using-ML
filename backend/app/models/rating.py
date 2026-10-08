from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, SCHEMA_NAME

if TYPE_CHECKING:
    from app.models.movie import Movie
    from app.models.profile import Profile


class Rating(Base):
    """User rating for a movie (0.5 to 5.0 stars)."""

    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("profile_id", "movie_id", name="uq_profile_movie_rating"),
        CheckConstraint("rating >= 0.5 AND rating <= 5.0", name="ck_rating_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey(f"{SCHEMA_NAME}.profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{SCHEMA_NAME}.movies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rating: Mapped[float] = mapped_column(Float, nullable=False)
    item_idx: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="ratings")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="ratings")

    def __repr__(self) -> str:
        return f"<Rating(profile='{self.profile_id}', movie={self.movie_id}, rating={self.rating})>"
