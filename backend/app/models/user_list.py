from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, SCHEMA_NAME

if TYPE_CHECKING:
    from app.models.movie import Movie
    from app.models.profile import Profile


class UserList(Base):
    """Profile watchlist and favorites collection."""

    __tablename__ = "user_lists"
    __table_args__ = (
        UniqueConstraint("profile_id", "movie_id", "list_type", name="uq_profile_movie_list_type"),
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
    list_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="watchlist",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="user_lists")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="user_lists")

    def __repr__(self) -> str:
        return f"<UserList(profile='{self.profile_id}', movie={self.movie_id}, type='{self.list_type}')>"
