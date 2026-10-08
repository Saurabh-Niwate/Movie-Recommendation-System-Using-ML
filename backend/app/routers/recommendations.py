from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.recommendation import (
    RecommendationItem,
    BecauseYouLikedResponse,
    AlsoWatchedItem,
    GenreCarousel,
)
from app.services.recommendation_service import recommendation_service

router = APIRouter(tags=["Recommendations"])


@router.get("", response_model=List[RecommendationItem])
@router.get("/", response_model=List[RecommendationItem], include_in_schema=False)
def get_recommendations(
    profile_id: str = Query(..., description="Active user profile ID"),
    model: str = Query("funk_svd", description="Model algorithm: funk_svd or item_knn"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get personalized recommendations. Returns 403 Forbidden if cold-start profile has <6 ratings."""
    return recommendation_service.get_recommendations(
        db=db,
        profile_id=profile_id,
        model_name=model,
        limit=limit,
    )


@router.get("/billboard", response_model=RecommendationItem)
def get_billboard(
    profile_id: str = Query(..., description="Active user profile ID"),
    db: Session = Depends(get_db),
):
    """Retrieve hero billboard movie recommendation for active profile."""
    return recommendation_service.get_billboard(db, profile_id=profile_id)


@router.get("/because-you-liked", response_model=BecauseYouLikedResponse)
def get_because_you_liked(
    profile_id: str = Query(..., description="Active user profile ID"),
    db: Session = Depends(get_db),
):
    """Retrieve 'Because you liked [Movie]' row based on profile's highest-rated movie and Item-KNN neighbors."""
    return recommendation_service.get_because_you_liked(db, profile_id=profile_id)


@router.get("/also-watched/{movie_id}", response_model=List[AlsoWatchedItem])
def get_also_watched(
    movie_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Retrieve 'Users also watched' items computed via Association Rules co-occurrence Lift."""
    return recommendation_service.get_also_watched(db, movie_id=movie_id, limit=limit)


@router.get("/genres", response_model=List[GenreCarousel])
def get_genre_carousels(
    profile_id: Optional[str] = Query(None, description="Optional profile ID"),
    db: Session = Depends(get_db),
):
    """Retrieve curated genre carousels for the browse page."""
    return recommendation_service.get_genre_carousels(db, profile_id=profile_id)
