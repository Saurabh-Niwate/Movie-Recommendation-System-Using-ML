from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_optional_current_user
from app.schemas.watchlist import (
    WatchlistItemResponse,
    WatchlistActionResponse,
    WatchlistCreateRequest,
)
from app.services.watchlist_service import watchlist_service

router = APIRouter(tags=["Watchlist"])


# =====================================================================
# Profile-Scoped Watchlist Endpoints (/profiles/{profile_id}/watchlist)
# =====================================================================

@router.get(
    "/profiles/{profile_id}/watchlist",
    response_model=List[WatchlistItemResponse],
    summary="List saved movies for a profile",
)
def get_profile_watchlist(
    profile_id: str,
    list_type: str = Query("watchlist", description="List type filter (watchlist or favorites)"),
    db: Session = Depends(get_db),
):
    """List enriched saved titles in a user profile's watchlist."""
    items = watchlist_service.get_watchlist(db, profile_id=profile_id, list_type=list_type)
    for it in items:
        if it.poster_path and not it.poster_path.startswith("http"):
            mid = it.movie_id or it.id
            it.poster_path = f"https://image.tmdb.org/t/p/w500/{mid}.jpg"
    return items


@router.post(
    "/profiles/{profile_id}/watchlist",
    response_model=WatchlistActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add movie to profile watchlist via body",
)
def add_to_profile_watchlist_body(
    profile_id: str,
    payload: WatchlistCreateRequest,
    list_type: str = Query("watchlist"),
    db: Session = Depends(get_db),
):
    """Add movie to profile watchlist via JSON body payload."""
    mid = payload.movie_id or payload.id
    if mid is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="movie_id or id is required in request body",
        )
    return watchlist_service.add_to_watchlist(
        db, profile_id=profile_id, movie_id=mid, list_type=payload.list_type or list_type
    )


@router.post(
    "/profiles/{profile_id}/watchlist/{movie_id}",
    response_model=WatchlistActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add movie to profile watchlist",
)
def add_to_profile_watchlist(
    profile_id: str,
    movie_id: int,
    list_type: str = Query("watchlist"),
    db: Session = Depends(get_db),
):
    """Add a movie title to a profile's watchlist (HTTP 201)."""
    return watchlist_service.add_to_watchlist(
        db, profile_id=profile_id, movie_id=movie_id, list_type=list_type
    )


@router.delete(
    "/profiles/{profile_id}/watchlist/{movie_id}",
    response_model=WatchlistActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove movie from profile watchlist",
)
def remove_from_profile_watchlist(
    profile_id: str,
    movie_id: int,
    list_type: str = Query("watchlist"),
    db: Session = Depends(get_db),
):
    """Remove a movie title from a profile's watchlist (HTTP 200)."""
    return watchlist_service.remove_from_watchlist(
        db, profile_id=profile_id, movie_id=movie_id, list_type=list_type
    )


# =====================================================================
# Root Watchlist Endpoints (/watchlist)
# =====================================================================

LEGACY_PROFILES = {"neel", "nitin", "mukesh", "alex", "demo"}


def _extract_profile_id(
    query_id: Optional[str] = None,
    header_id: Optional[str] = None,
    body_id: Optional[str] = None,
    current_user: Optional[User] = None,
    authorization: Optional[str] = None,
) -> str:
    if current_user:
        return current_user.id
    pid = body_id or query_id or header_id
    if pid and pid.lower() in LEGACY_PROFILES:
        return pid.lower()
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


@router.get(
    "/watchlist",
    response_model=List[WatchlistItemResponse],
    summary="List watchlist items via root path",
)
def get_root_watchlist(
    profile_id: Optional[str] = Query(None, description="Target profile ID"),
    x_profile_id: Optional[str] = Header(None, alias="x-profile-id"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    list_type: str = Query("watchlist"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """List saved movies using root path with profile_id query, header, or Bearer auth."""
    pid = _extract_profile_id(profile_id, x_profile_id, current_user=current_user, authorization=authorization)
    items = watchlist_service.get_watchlist(db, profile_id=pid, list_type=list_type)
    for it in items:
        if it.poster_path and not it.poster_path.startswith("http"):
            mid = it.movie_id or it.id
            it.poster_path = f"https://image.tmdb.org/t/p/w500/{mid}.jpg"
    return items


@router.post(
    "/watchlist",
    response_model=WatchlistActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add movie to watchlist via JSON body",
)
def add_root_watchlist(
    payload: WatchlistCreateRequest,
    profile_id: Optional[str] = Query(None),
    x_profile_id: Optional[str] = Header(None, alias="x-profile-id"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Add movie to watchlist via root endpoint using request body."""
    pid = _extract_profile_id(profile_id, x_profile_id, payload.profile_id, current_user=current_user, authorization=authorization)
    mid = payload.movie_id or payload.id
    if mid is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="movie_id or id is required in request body",
        )
    return watchlist_service.add_to_watchlist(
        db, profile_id=pid, movie_id=mid, list_type=payload.list_type or "watchlist"
    )


@router.post(
    "/watchlist/{movie_id}",
    response_model=WatchlistActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add movie to watchlist via path and query/header profile",
)
def add_root_watchlist_by_path(
    movie_id: int,
    profile_id: Optional[str] = Query(None),
    x_profile_id: Optional[str] = Header(None, alias="x-profile-id"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    list_type: str = Query("watchlist"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Add movie to watchlist using path movie_id and query/header profile or Bearer auth."""
    pid = _extract_profile_id(profile_id, x_profile_id, current_user=current_user, authorization=authorization)
    return watchlist_service.add_to_watchlist(
        db, profile_id=pid, movie_id=movie_id, list_type=list_type
    )


@router.delete(
    "/watchlist/{movie_id}",
    response_model=WatchlistActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove movie from watchlist via root path",
)
def remove_root_watchlist_by_path(
    movie_id: int,
    profile_id: Optional[str] = Query(None),
    x_profile_id: Optional[str] = Header(None, alias="x-profile-id"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    list_type: str = Query("watchlist"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Remove movie from watchlist using path movie_id and query/header profile or Bearer auth."""
    pid = _extract_profile_id(profile_id, x_profile_id, current_user=current_user, authorization=authorization)
    return watchlist_service.remove_from_watchlist(
        db, profile_id=pid, movie_id=movie_id, list_type=list_type
    )
