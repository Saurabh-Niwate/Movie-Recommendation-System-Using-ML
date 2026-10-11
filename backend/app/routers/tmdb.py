"""TMDB router providing external metadata proxying, trailer extraction, and status using API Read Access Token."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.movie import Movie
from app.schemas.movie import MovieTrailerResponse
from app.services.tmdb import tmdb_service

router = APIRouter(tags=["TMDB"])


@router.get("/status")
def get_tmdb_status() -> Dict[str, Any]:
    """Return status of TMDB integration, auth mode, and whether live access or offline fallback is active."""
    return {
        "is_offline": tmdb_service.is_offline,
        "auth_mode": "bearer_read_access_token" if not tmdb_service.is_offline else "offline_fallback",
        "has_token": bool(settings.effective_tmdb_read_token),
        "base_url": settings.tmdb_base_url,
        "image_base_url": settings.tmdb_image_base_url,
    }


@router.get("/search")
def search_tmdb(
    query: str = Query(..., min_length=1, description="Movie search title"),
    year: Optional[int] = Query(None, description="Optional release year"),
) -> List[Dict[str, Any]]:
    """Search TMDB catalog using API Read Access Token (falls back seamlessly if offline)."""
    return tmdb_service.search_movies_sync(query=query, year=year)


@router.get("/movie/{tmdb_id}")
def get_tmdb_movie_details(
    tmdb_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Fetch movie details and credits from TMDB using API Read Access Token."""
    if tmdb_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with TMDB ID {tmdb_id} not found",
        )
    details = tmdb_service.get_movie_details_sync(tmdb_id)
    if not details or not details.get("title"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with TMDB ID {tmdb_id} not found",
        )

    # Ensure both id and tmdb_id are present in response dictionary
    details.setdefault("id", tmdb_id)
    details["tmdb_id"] = details.get("tmdb_id") or tmdb_id

    movie = db.query(Movie).filter(or_(Movie.tmdb_id == tmdb_id, Movie.id == tmdb_id)).first()
    if movie:
        details.setdefault("movie_id", movie.id)

    return details


@router.get("/movie/{tmdb_id}/trailer", response_model=MovieTrailerResponse, summary="Get YouTube trailer embed metadata by TMDB ID")
def get_tmdb_movie_trailer(
    tmdb_id: int,
    db: Session = Depends(get_db),
):
    """Alias route to retrieve YouTube trailer video by TMDB ID."""
    if tmdb_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid TMDB ID {tmdb_id}",
        )
    movie = db.query(Movie).filter(or_(Movie.tmdb_id == tmdb_id, Movie.id == tmdb_id)).first()
    movie_id = movie.id if movie else None
    title = movie.title if movie else None

    trailer = tmdb_service.get_movie_trailer(
        movie_id=movie_id,
        tmdb_id=tmdb_id,
        title=title,
    )
    if not trailer or not trailer.get("key"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trailer for TMDB ID {tmdb_id} not found",
        )
    return trailer
