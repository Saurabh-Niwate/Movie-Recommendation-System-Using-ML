"""User database model for single-user authentication and account state."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.rating import Rating
    from app.models.user_list import UserList


class User(Base):
    """User account entity representing a single authenticated user account."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Telemetry and cold-start state
    ratings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_cold_start: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 32-dimensional latent taste vector from Funk-SVD fold-in
    taste_vector: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships linked via profile_id == user.id
    ratings: Mapped[List["Rating"]] = relationship(
        "Rating",
        primaryjoin="foreign(Rating.profile_id) == User.id",
        cascade="all, delete-orphan",
        overlaps="profile,ratings",
    )
    user_lists: Mapped[List["UserList"]] = relationship(
        "UserList",
        primaryjoin="foreign(UserList.profile_id) == User.id",
        cascade="all, delete-orphan",
        overlaps="profile,user_lists",
    )

    def __repr__(self) -> str:
        return f"<User(id='{self.id}', email='{self.email}', ratings={self.ratings_count}, cold_start={self.is_cold_start})>"
