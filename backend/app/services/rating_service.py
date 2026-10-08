import time
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.movie import Movie
from app.models.rating import Rating
from app.repositories.profile_repository import profile_repository
from app.repositories.movie_repository import movie_repository
from app.repositories.rating_repository import rating_repository
from app.infra.model_registry import get_model_registry
from app.services.cache import get_cache_service


class RatingService:
    """Service handling rating persistence, online fold-in vector solving, and cache invalidation."""

    def submit_rating(
        self,
        db: Session,
        profile_id: str,
        movie_id: int,
        rating_value: float,
    ) -> Dict[str, Any]:
        """Submit a movie rating, perform instantaneous online fold-in, and invalidate profile cache."""
        profile = profile_repository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found",
            )

        movie = movie_repository.get_by_id(db, movie_id)
        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with ID {movie_id} not found",
            )

        if rating_value < 0.5 or rating_value > 5.0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Rating must be between 0.5 and 5.0 stars",
            )

        # 1. Upsert rating record in PostgreSQL cinematch.ratings
        rating_record, is_created = rating_repository.upsert_rating(
            db=db,
            profile_id=profile.id,
            movie_id=movie.id,
            rating_value=rating_value,
            item_idx=movie.item_idx,
        )

        # 2. Update profile rating counter & cold-start gating status
        new_count = rating_repository.count_by_profile(db, profile.id)
        is_cold_start = new_count < 6
        profile_repository.update_cold_start(
            db=db,
            profile=profile,
            ratings_count=new_count,
            is_cold_start=is_cold_start,
        )

        # 3. Closed-form online fold-in: update user latent vector in <50ms without retraining
        t0 = time.perf_counter()
        reg = get_model_registry()
        user_ratings_dict = rating_repository.get_user_ratings_dict(db, profile.id)
        b_u, p_u = reg.fold_in_profile(profile.id, user_ratings_dict)
        fold_in_duration_ms = (time.perf_counter() - t0) * 1000.0

        # 4. Immediate cache invalidation for the rated profile
        cache = get_cache_service()
        evicted_keys = cache.invalidate_profile(profile.id)

        unlocked = not is_cold_start
        return {
            "status": "ok",
            "ratings_count": new_count,
            "unlocked": unlocked,
            "fold_in_ms": round(fold_in_duration_ms, 3),
            "evicted_cache_entries": evicted_keys,
            "message": "Recommendations unlocked!" if unlocked and is_created and new_count == 6 else "Rating saved",
        }

    def get_ratings(self, db: Session, profile_id: str) -> List[Rating]:
        """Fetch all ratings submitted by a profile."""
        profile = profile_repository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found",
            )
        return rating_repository.get_user_ratings(db, profile_id)


rating_service = RatingService()
