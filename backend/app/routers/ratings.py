from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_optional_current_user
from app.schemas.rating import ProfileRatingCreate, RatingResponse, RatingItem
from app.services.rating_service import rating_service

router = APIRouter(tags=["Ratings"])


@router.post("", response_model=RatingResponse)
@router.post("/", response_model=RatingResponse, include_in_schema=False)
def create_rating(
    payload: ProfileRatingCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    """Save rating, trigger closed-form online fold-in in <50ms, and invalidate profile cache."""
    target_id = (current_user.id if current_user else None) or payload.profile_id
    if not target_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # If current_user is authenticated and payload.profile_id is provided but differs from current_user.id,
    # prevent IDOR/spoofing by enforcing target_id = current_user.id
    if current_user and payload.profile_id and payload.profile_id != current_user.id:
        target_id = current_user.id

    return rating_service.submit_rating(
        db=db,
        profile_id=target_id,
        movie_id=payload.movie_id,
        rating_value=payload.rating,
    )


@router.get("", response_model=List[RatingItem])
@router.get("/", response_model=List[RatingItem], include_in_schema=False)
def get_ratings(
    profile_id: Optional[str] = Query(None, description="Profile ID to fetch ratings for"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    """Retrieve ratings for a specific profile or authenticated user."""
    target_id = (current_user.id if current_user else None) or profile_id
    if not target_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return rating_service.get_ratings(db, profile_id=target_id)
