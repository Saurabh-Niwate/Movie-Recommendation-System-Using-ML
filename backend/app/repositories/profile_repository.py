from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.profile import Profile


class ProfileRepository:
    """Repository handling Profile database operations."""

    def get_all(self, db: Session) -> List[Profile]:
        return db.query(Profile).order_by(Profile.is_demo.desc(), Profile.id.asc()).all()

    def get_by_id(self, db: Session, profile_id: str) -> Optional[Profile]:
        return db.query(Profile).filter(Profile.id == profile_id).first()

    def update_cold_start(
        self, db: Session, profile: Profile, ratings_count: int, is_cold_start: bool
    ) -> Profile:
        profile.ratings_count = ratings_count
        profile.is_cold_start = is_cold_start
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile


profile_repository = ProfileRepository()
