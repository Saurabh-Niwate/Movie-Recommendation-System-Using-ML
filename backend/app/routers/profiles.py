from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.profile import ProfileResponse, ProfileDetailResponse
from app.schemas.rating import RatingCreate, RatingResponse, RatingItem
from app.schemas.recommendation import RecommendationItem
from app.services.profile_service import profile_service
from app.services.rating_service import rating_service
from app.services.recommendation_service import recommendation_service

router = APIRouter(tags=["Profiles"])


@router.get("", response_model=List[ProfileResponse])
@router.get("/", response_model=List[ProfileResponse], include_in_schema=False)
def list_profiles(db: Session = Depends(get_db)):
    """List all available profiles (demo users Neel, Nitin, and cold-start Mukesh)."""
    return profile_service.list_profiles(db)


@router.get("/{profile_id}", response_model=ProfileDetailResponse)
def get_profile(profile_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed metadata for a specific profile."""
    profile = profile_service.get_profile(db, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_id}' not found",
        )
    return profile


@router.get("/{profile_id}/recommendations", response_model=List[RecommendationItem])
def get_profile_recommendations(
    profile_id: str,
    model: str = Query("funk_svd", description="Model algorithm: funk_svd or item_knn"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get personalized recommendations for profile. Returns 403 if profile is cold-start with <6 ratings."""
    return recommendation_service.get_recommendations(
        db=db,
        profile_id=profile_id,
        model_name=model,
        limit=limit,
    )


@router.post("/{profile_id}/ratings", response_model=RatingResponse)
def submit_profile_rating(
    profile_id: str,
    payload: RatingCreate,
    db: Session = Depends(get_db),
):
    """Submit a rating for a profile, run online fold-in in <50ms, and invalidate recommendations cache."""
    return rating_service.submit_rating(
        db=db,
        profile_id=profile_id,
        movie_id=payload.movie_id,
        rating_value=payload.rating,
    )


@router.get("/{profile_id}/ratings", response_model=List[RatingItem])
def get_profile_ratings(
    profile_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve all ratings submitted by a profile."""
    return rating_service.get_ratings(db, profile_id)
