from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.repositories.profile_repository import profile_repository
from app.routers.auth import get_optional_current_user
from app.schemas.recommendation import (
    RecommendationItem,
    BecauseYouLikedResponse,
    AlsoWatchedItem,
    GenreCarousel,
)
from app.services.recommendation_service import recommendation_service

router = APIRouter(tags=["Recommendations"])


@router.get("", response_model=None)
@router.get("/", response_model=None, include_in_schema=False)
def get_recommendations(
    profile_id: Optional[str] = Query(None, description="Active user profile ID"),
    model: str = Query("funk_svd", description="Model algorithm: funk_svd or item_knn"),
    limit: int = Query(20, ge=1, le=100),
    format: Optional[str] = Query(None, description="Optional format: envelope or list"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Get personalized recommendations. Returns 403 Forbidden if cold-start profile has <6 ratings."""
    target_id = (current_user.id if current_user else None) or profile_id
    if not target_id:
        if authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token required or invalid",
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="profile_id query parameter or Bearer authorization required",
        )

    # Strictly enforce cold-start gating: 403 Forbidden when ratings_count < 6
    user = db.query(User).filter(User.id == target_id).first()
    if user:
        if user.ratings_count < 6 or user.is_cold_start:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cold start profile requires at least 6 ratings",
            )
    else:
        profile = profile_repository.get_by_id(db, target_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Profile '{target_id}' not found")
        if profile.ratings_count < 6 or profile.is_cold_start:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cold start profile requires at least 6 ratings",
            )

    raw_items = recommendation_service.get_recommendations(
        db=db,
        profile_id=target_id,
        model_name=model,
        limit=limit,
    )

    serialized_items = []
    for item in raw_items:
        d = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        d["movie_id"] = d.get("id")
        d["match_percentage"] = d.get("match_percent", 90)
        serialized_items.append(d)

    if format == "list":
        return serialized_items

    return {
        "user_id": target_id,
        "profile_id": target_id,
        "model": model,
        "total_candidates": len(serialized_items),
        "items": serialized_items,
    }


@router.get("/billboard", response_model=RecommendationItem)
def get_billboard(
    profile_id: Optional[str] = Query(None, description="Active user profile ID"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve hero billboard movie recommendation for active profile."""
    target_id = (current_user.id if current_user else None) or profile_id
    if not target_id:
        if authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token required or invalid",
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="profile_id is required",
        )

    user = db.query(User).filter(User.id == target_id).first()
    if user and (user.ratings_count < 6 or user.is_cold_start):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cold start profile requires at least 6 ratings",
        )

    return recommendation_service.get_billboard(db, profile_id=target_id)


@router.get("/because-you-liked", response_model=BecauseYouLikedResponse)
def get_because_you_liked(
    profile_id: Optional[str] = Query(None, description="Active user profile ID"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve 'Because you liked [Movie]' row based on profile's highest-rated movie and Item-KNN neighbors."""
    target_id = (current_user.id if current_user else None) or profile_id
    if not target_id:
        if authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token required or invalid",
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="profile_id is required",
        )

    user = db.query(User).filter(User.id == target_id).first()
    if user and (user.ratings_count < 6 or user.is_cold_start):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cold start profile requires at least 6 ratings",
        )

    return recommendation_service.get_because_you_liked(db, profile_id=target_id)


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
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve curated genre carousels for the browse page."""
    target_id = (current_user.id if current_user else None) or profile_id
    return recommendation_service.get_genre_carousels(db, profile_id=target_id)
