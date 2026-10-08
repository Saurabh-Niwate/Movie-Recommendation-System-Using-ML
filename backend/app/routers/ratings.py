from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.rating import ProfileRatingCreate, RatingResponse, RatingItem
from app.services.rating_service import rating_service

router = APIRouter(tags=["Ratings"])


@router.post("", response_model=RatingResponse)
@router.post("/", response_model=RatingResponse, include_in_schema=False)
def create_rating(
    payload: ProfileRatingCreate,
    db: Session = Depends(get_db),
):
    """Save rating, trigger closed-form online fold-in in <50ms, and invalidate profile cache."""
    if not payload.profile_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="profile_id is required",
        )
    return rating_service.submit_rating(
        db=db,
        profile_id=payload.profile_id,
        movie_id=payload.movie_id,
        rating_value=payload.rating,
    )


@router.get("", response_model=List[RatingItem])
@router.get("/", response_model=List[RatingItem], include_in_schema=False)
def get_ratings(
    profile_id: str = Query(..., description="Profile ID to fetch ratings for"),
    db: Session = Depends(get_db),
):
    """Retrieve ratings for a specific profile."""
    return rating_service.get_ratings(db, profile_id=profile_id)
