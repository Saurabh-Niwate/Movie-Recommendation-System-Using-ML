import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.movie import Movie
from app.schemas.movie import MovieSummary, MovieDetail, MovieSearchResponse, MovieTrailerResponse
from app.services.movie_service import movie_service
from app.services.tmdb import tmdb_service, TMDB_ID_MAP

router = APIRouter(tags=["Movies"])


class MovieCatalogResponse(BaseModel):
    items: List[MovieSummary]
    total: int
    genre: Optional[str] = None


@router.get("", response_model=MovieCatalogResponse, summary="List catalog movies with filtering and pagination")
@router.get("/", response_model=MovieCatalogResponse, include_in_schema=False)
def list_movies(
    genre: Optional[str] = Query(None, description="Filter movies by genre"),
    search: Optional[str] = Query(None, description="Search query matching movie title"),
    sort: Optional[str] = Query("top_rated", description="Sort order: top_rated, recent, popular"),
    limit: int = Query(24, ge=1, le=250, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """Catalog listing endpoint supporting genre filtering, title search, and sorting."""
    query = db.query(Movie)

    if genre and genre.strip():
        clean_genre = genre.strip()
        query = query.filter(cast(Movie.genres, String).ilike(f"%{clean_genre}%"))

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Movie.title.ilike(term),
                Movie.title_raw.ilike(term),
                Movie.director.ilike(term),
            )
        )

    total = query.count()

    if sort == "recent":
        query = query.order_by(Movie.year.desc(), Movie.id.asc())
    elif sort == "popular":
        query = query.order_by(Movie.vote_count.desc(), Movie.vote_average.desc(), Movie.id.asc())
    else:  # "top_rated" or default
        query = query.order_by(Movie.vote_average.desc(), Movie.vote_count.desc(), Movie.id.asc())

    movies = query.offset(offset).limit(limit).all()
    return MovieCatalogResponse(
        items=[MovieSummary.model_validate(m) for m in movies],
        total=total,
        genre=genre,
    )


@router.get("/starter", response_model=List[MovieSummary])
def get_starter_grid(
    limit: int = Query(24, ge=6, le=60),
    db: Session = Depends(get_db),
):
    """Return 24 diverse popular titles for cold-start onboarding rating."""
    movies = movie_service.get_starter_grid(db, limit=limit)
    return movies


@router.get("/search", response_model=None)
def search_movies(
    request: Request,
    q: Optional[str] = Query(None, description="Search term for movie title"),
    genre: Optional[str] = Query(None, description="Optional genre filter"),
    limit: int = Query(30, ge=1, le=250),
    format: Optional[str] = Query(None, description="Optional response format"),
    db: Session = Depends(get_db),
):
    """Search movie catalog by title and genre."""
    query_str = (q or "").strip()
    if query_str:
        results = movie_service.search_movies(db, query=query_str, limit=limit)
    else:
        # If no query string, return catalog movies up to limit
        query = db.query(Movie)
        if genre and genre.strip():
            clean_genre = genre.strip()
            query = query.filter(cast(Movie.genres, String).ilike(f"%{clean_genre}%"))
        results = query.order_by(Movie.vote_count.desc(), Movie.vote_average.desc(), Movie.id.asc()).limit(limit).all()

    if genre and genre.strip():
        g_clean = genre.strip().lower()
        results = [m for m in results if any(g_clean in str(g).lower() for g in (m.genres or []))]

    items = [MovieSummary.model_validate(m) for m in results]

    if format == "envelope":
        return MovieSearchResponse(items=items, total=len(items))

    if (
        os.environ.get("USE_LIVE_BACKEND") == "1"
        or format == "list"
        or "limit" in request.query_params
        or "genre" in request.query_params
        or not query_str
    ):
        return items

    return MovieSearchResponse(items=items, total=len(items))


@router.get("/{movie_id}", response_model=MovieDetail)
def get_movie_detail(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve full movie details including synopsis, genres, cast, poster, and backdrop."""
    if movie_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found",
        )
    movie = movie_service.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found",
        )
    return movie


@router.get("/{movie_id}/trailer", response_model=MovieTrailerResponse, summary="Get YouTube trailer embed metadata for a movie")
def get_movie_trailer(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve YouTube trailer video embed URLs and keys for a movie."""
    if movie_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found",
        )
    movie = movie_service.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found",
        )

    tmdb_id = movie.tmdb_id
    if (tmdb_id is None or tmdb_id >= 100000) and movie.id in TMDB_ID_MAP:
        tmdb_id = TMDB_ID_MAP[movie.id]

    trailer = tmdb_service.get_movie_trailer(
        movie_id=movie.id,
        tmdb_id=tmdb_id,
        title=movie.title,
    )
    if not trailer or not trailer.get("key"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trailer for movie ID {movie_id} not found",
        )
    return trailer
