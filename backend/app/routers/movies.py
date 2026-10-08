from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.movie import MovieSummary, MovieDetail, MovieSearchResponse
from app.services.movie_service import movie_service

router = APIRouter(tags=["Movies"])


@router.get("/starter", response_model=List[MovieSummary])
def get_starter_grid(
    limit: int = Query(24, ge=6, le=60),
    db: Session = Depends(get_db),
):
    """Return 24 diverse popular titles for cold-start onboarding rating."""
    movies = movie_service.get_starter_grid(db, limit=limit)
    return movies


@router.get("/search", response_model=MovieSearchResponse)
def search_movies(
    q: str = Query("", description="Search term for movie title"),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search movie catalog by title."""
    results = movie_service.search_movies(db, query=q, limit=limit)
    return MovieSearchResponse(items=[MovieSummary.model_validate(m) for m in results], total=len(results))


@router.get("/{movie_id}", response_model=MovieDetail)
def get_movie_detail(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve full movie details including synopsis, genres, cast, poster, and backdrop."""
    movie = movie_service.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found",
        )
    return movie
