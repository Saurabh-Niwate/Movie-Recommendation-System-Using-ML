from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.rating import Rating


class RatingRepository:
    """Repository handling Rating operations in cinematch.ratings."""

    def get_user_ratings(self, db: Session, profile_id: str) -> List[Rating]:
        return (
            db.query(Rating)
            .filter(Rating.profile_id == profile_id)
            .order_by(Rating.created_at.desc())
            .all()
        )

    def get_user_ratings_dict(self, db: Session, profile_id: str) -> Dict[int, float]:
        """Return mapping of item_idx -> rating for all rated items with valid item_idx."""
        ratings = (
            db.query(Rating.item_idx, Rating.rating)
            .filter(Rating.profile_id == profile_id, Rating.item_idx.isnot(None))
            .all()
        )
        return {int(r[0]): float(r[1]) for r in ratings if r[0] is not None}

    def upsert_rating(
        self,
        db: Session,
        profile_id: str,
        movie_id: int,
        rating_value: float,
        item_idx: Optional[int],
    ) -> Tuple[Rating, bool]:
        """Create or update a rating record. Returns (rating, is_created)."""
        existing = (
            db.query(Rating)
            .filter(Rating.profile_id == profile_id, Rating.movie_id == movie_id)
            .first()
        )
        if existing:
            existing.rating = float(rating_value)
            existing.item_idx = item_idx
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing, False

        new_rating = Rating(
            profile_id=profile_id,
            movie_id=movie_id,
            rating=float(rating_value),
            item_idx=item_idx,
        )
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        return new_rating, True

    def count_by_profile(self, db: Session, profile_id: str) -> int:
        return db.query(Rating).filter(Rating.profile_id == profile_id).count()


rating_repository = RatingRepository()
