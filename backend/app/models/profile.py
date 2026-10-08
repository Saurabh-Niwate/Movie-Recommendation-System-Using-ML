from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.rating import Rating
    from app.models.user_list import UserList


class Profile(Base):
    """User profile entity representing demo users (Neel, Nitin) or cold-start users (Mukesh)."""

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    taste_cluster: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ML user index (0..N-1) in MovieLens 1M matrix, if mapped
    user_idx: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ratings_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_cold_start: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

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

    # Relationships
    ratings: Mapped[List["Rating"]] = relationship(
        "Rating",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    user_lists: Mapped[List["UserList"]] = relationship(
        "UserList",
        back_populates="profile",
        cascade="all, delete-orphan",
    )

    @property
    def genres(self) -> List[str]:
        if self.id == "neel":
            return ["Action", "Sci-Fi", "Adventure"]
        if self.id == "nitin":
            return ["Drama", "Romance"]
        return []

    @property
    def color_accent(self) -> str:
        if self.id == "neel":
            return "from-cyan-600 to-blue-700"
        if self.id == "nitin":
            return "from-purple-600 to-pink-700"
        return "from-amber-600 to-emerald-700"

    def __repr__(self) -> str:
        return f"<Profile(id='{self.id}', name='{self.name}', cold_start={self.is_cold_start})>"

