"""TMDB router providing external metadata proxying and status using API Read Access Token."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
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
) -> Dict[str, Any]:
    """Fetch movie details and credits from TMDB using API Read Access Token."""
    details = tmdb_service.get_movie_details_sync(tmdb_id)
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with TMDB ID {tmdb_id} not found",
        )
    return details
