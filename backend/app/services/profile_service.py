from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.profile import Profile
from app.repositories.profile_repository import profile_repository


class ProfileService:
    """Service managing profile retrieval and cold-start verification."""

    def list_profiles(self, db: Session) -> List[Profile]:
        return profile_repository.get_all(db)

    def get_profile(self, db: Session, profile_id: str) -> Optional[Profile]:
        return profile_repository.get_by_id(db, profile_id)

    def is_cold_start(self, profile: Profile) -> bool:
        """Evaluate cold-start condition (less than 6 ratings)."""
        return profile.is_cold_start or profile.ratings_count < 6


profile_service = ProfileService()
