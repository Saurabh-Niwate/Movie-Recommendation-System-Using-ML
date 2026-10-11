import re
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.profile import Profile
from app.models.rating import Rating
from app.models.user import User
from app.models.user_list import UserList
from app.schemas.profile import ProfileResponse, ProfileDetailResponse
from app.schemas.rating import RatingCreate, RatingResponse, RatingItem
from app.schemas.recommendation import RecommendationItem
from app.schemas.watchlist import WatchlistItemResponse, WatchlistActionResponse
from app.services.cache import get_cache_service
from app.services.profile_service import profile_service
from app.services.rating_service import rating_service
from app.services.recommendation_service import recommendation_service
from app.services.watchlist_service import watchlist_service

router = APIRouter(tags=["Profiles"])


class ProfileCreate(BaseModel):
    id: Optional[str] = None
    name: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    taste_cluster: Optional[str] = None
    is_demo: bool = False


class ProfileResetRequest(BaseModel):
    profile_id: Optional[str] = None


class ProfileResetResponse(BaseModel):
    status: str = "reset"
    profile_id: Optional[str] = "all"


@router.get("", response_model=List[ProfileResponse])
@router.get("/", response_model=List[ProfileResponse], include_in_schema=False)
def list_profiles(db: Session = Depends(get_db)):
    """List all available profiles (demo users Neel, Nitin, and cold-start Mukesh)."""
    return profile_service.list_profiles(db)


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def register_profile(
    payload: ProfileCreate,
    db: Session = Depends(get_db),
):
    """Register a new user profile with cold-start gating enabled."""
    name_clean = payload.name.strip()
    if not name_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile name cannot be empty",
        )

    if payload.id and payload.id.strip():
        pid = payload.id.strip().lower()
        existing = db.query(Profile).filter(Profile.id == pid).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Profile '{pid}' already exists",
            )
    else:
        base_id = re.sub(r"[^a-zA-Z0-9_-]", "_", name_clean.lower())
        base_id = base_id.strip("_") or "user"
        candidate = base_id
        counter = 1
        while db.query(Profile).filter(Profile.id == candidate).first():
            candidate = f"{base_id}_{counter}"
            counter += 1
        pid = candidate

    avatar = (
        payload.avatar
        or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=300&q=80"
    )

    profile = Profile(
        id=pid,
        name=name_clean,
        avatar=avatar,
        bio=payload.bio or "Movie enthusiast",
        taste_cluster=payload.taste_cluster or "General",
        is_demo=payload.is_demo,
        ratings_count=0,
        is_cold_start=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/reset", response_model=ProfileResetResponse, status_code=status.HTTP_200_OK)
def reset_profiles(
    payload: Optional[ProfileResetRequest] = Body(None),
    db: Session = Depends(get_db),
):
    """Reset profile ratings and history back to baseline seed state (required by E2E test harness)."""
    target_id = payload.profile_id if payload else None
    cache = get_cache_service()

    try:
        from scripts.seed import seed_profiles_and_ratings, seed_demo_user_lists
    except ImportError:
        from backend.scripts.seed import seed_profiles_and_ratings, seed_demo_user_lists

    if target_id and target_id.strip():
        pid = target_id.strip().lower()
        if pid == "mukesh":
            db.query(Rating).filter(Rating.profile_id == "mukesh").delete()
            db.query(UserList).filter(UserList.profile_id == "mukesh").delete()
            mukesh = db.query(Profile).filter(Profile.id == "mukesh").first()
            if mukesh:
                mukesh.ratings_count = 0
                mukesh.is_cold_start = True
            mukesh_user = db.query(User).filter(User.id == "mukesh").first()
            if mukesh_user:
                mukesh_user.ratings_count = 0
                mukesh_user.is_cold_start = True
                mukesh_user.taste_vector = None
            db.commit()
        elif pid in ("neel", "nitin"):
            seed_profiles_and_ratings(db, reset=True)
            seed_demo_user_lists(db, reset=True)
            u = db.query(User).filter(User.id == pid).first()
            if u:
                u.taste_vector = None
                db.commit()
        else:
            db.query(Rating).filter(Rating.profile_id == pid).delete()
            db.query(UserList).filter(UserList.profile_id == pid).delete()
            db.query(Profile).filter(Profile.id == pid).delete()
            db.query(User).filter(User.id == pid).delete()
            db.commit()

        cache.invalidate_profile(pid)
        return ProfileResetResponse(status="reset", profile_id=pid)
    else:
        # Global reset: purge all test users and non-baseline profiles
        BASELINE_IDS = ["neel", "nitin", "mukesh", "alex", "demo"]

        # 1. Purge dynamically generated test users (usr_* or non-baseline users)
        test_users = db.query(User).filter(~User.id.in_(BASELINE_IDS)).all()
        for tu in test_users:
            db.query(Rating).filter(Rating.profile_id == tu.id).delete()
            db.query(UserList).filter(UserList.profile_id == tu.id).delete()
            db.query(Profile).filter(Profile.id == tu.id).delete()
            db.delete(tu)

        # 2. Purge non-baseline profiles
        extra_profiles = db.query(Profile).filter(~Profile.id.in_(BASELINE_IDS)).all()
        for ep in extra_profiles:
            db.query(Rating).filter(Rating.profile_id == ep.id).delete()
            db.query(UserList).filter(UserList.profile_id == ep.id).delete()
            db.delete(ep)
        db.commit()

        # 3. Reset Mukesh to cold-start 0 ratings
        db.query(Rating).filter(Rating.profile_id == "mukesh").delete()
        db.query(UserList).filter(UserList.profile_id == "mukesh").delete()
        mukesh = db.query(Profile).filter(Profile.id == "mukesh").first()
        if mukesh:
            mukesh.ratings_count = 0
            mukesh.is_cold_start = True
        mukesh_user = db.query(User).filter(User.id == "mukesh").first()
        if mukesh_user:
            mukesh_user.ratings_count = 0
            mukesh_user.is_cold_start = True
            mukesh_user.taste_vector = None

        # 4. Reset other baseline users (alex, demo)
        for base_id in ("alex", "demo"):
            bu = db.query(User).filter(User.id == base_id).first()
            if bu:
                bu.ratings_count = 0
                bu.is_cold_start = True
                bu.taste_vector = None
                db.query(Rating).filter(Rating.profile_id == base_id).delete()
                db.query(UserList).filter(UserList.profile_id == base_id).delete()

        # 5. Clear taste_vector on neel, nitin
        for base_id in ("neel", "nitin"):
            bu = db.query(User).filter(User.id == base_id).first()
            if bu:
                bu.taste_vector = None
        db.commit()

        # 6. Re-seed Neel & Nitin baseline ratings and lists
        seed_profiles_and_ratings(db, reset=True)
        seed_demo_user_lists(db, reset=True)

        cache.clear()
        return ProfileResetResponse(status="reset", profile_id="all")


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


@router.get("/{profile_id}/watchlist", response_model=List[WatchlistItemResponse])
def get_profile_watchlist(
    profile_id: str,
    list_type: str = Query("watchlist"),
    db: Session = Depends(get_db),
):
    """List movies saved in profile's watchlist."""
    return watchlist_service.get_watchlist(db, profile_id=profile_id, list_type=list_type)


@router.post(
    "/{profile_id}/watchlist/{movie_id}",
    response_model=WatchlistActionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_profile_watchlist(
    profile_id: str,
    movie_id: int,
    list_type: str = Query("watchlist"),
    db: Session = Depends(get_db),
):
    """Add movie to profile's watchlist (HTTP 201)."""
    return watchlist_service.add_to_watchlist(
        db, profile_id=profile_id, movie_id=movie_id, list_type=list_type
    )


@router.delete(
    "/{profile_id}/watchlist/{movie_id}",
    response_model=WatchlistActionResponse,
    status_code=status.HTTP_200_OK,
)
def remove_from_profile_watchlist(
    profile_id: str,
    movie_id: int,
    list_type: str = Query("watchlist"),
    db: Session = Depends(get_db),
):
    """Remove movie from profile's watchlist (HTTP 200)."""
    return watchlist_service.remove_from_watchlist(
        db, profile_id=profile_id, movie_id=movie_id, list_type=list_type
    )


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
