from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.movie import Movie
from app.models.user_list import UserList
from app.repositories.movie_repository import movie_repository
from app.repositories.profile_repository import profile_repository
from app.repositories.user_list_repository import user_list_repository
from app.schemas.watchlist import WatchlistItemResponse, WatchlistActionResponse


class WatchlistService:
    """Service handling watchlist operations, enriched metadata retrieval, and validation."""

    def get_watchlist(
        self, db: Session, profile_id: str, list_type: str = "watchlist"
    ) -> List[WatchlistItemResponse]:
        """Retrieve enriched movies in a user's watchlist or list.
        
        Raises 404 if profile does not exist.
        """
        profile = profile_repository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found",
            )

        items = (
            db.query(UserList, Movie)
            .join(Movie, UserList.movie_id == Movie.id)
            .filter(UserList.profile_id == profile_id, UserList.list_type == list_type)
            .order_by(UserList.created_at.desc(), UserList.id.desc())
            .all()
        )

        response_items: List[WatchlistItemResponse] = []
        for user_list_entry, movie in items:
            response_items.append(
                WatchlistItemResponse(
                    id=movie.id,
                    movie_id=movie.id,
                    title=movie.title,
                    poster_path=movie.poster_path,
                    backdrop_path=movie.backdrop_path,
                    release_year=movie.year,
                    year=movie.year,
                    genres=movie.genres or [],
                    vote_average=movie.vote_average,
                    vote_count=movie.vote_count,
                    added_at=user_list_entry.created_at,
                    synopsis=movie.effective_synopsis(),
                    overview=movie.overview,
                    tmdb_id=movie.tmdb_id,
                    director=movie.director,
                    runtime=movie.runtime,
                    list_type=user_list_entry.list_type,
                )
            )
        return response_items

    def add_to_watchlist(
        self, db: Session, profile_id: str, movie_id: int, list_type: str = "watchlist"
    ) -> WatchlistActionResponse:
        """Add movie to user's watchlist. Handles duplicates cleanly without crashing.
        
        Raises 404 if profile or movie does not exist.
        """
        profile = profile_repository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found",
            )

        movie = movie_repository.get_by_id(db, movie_id)
        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with ID {movie_id} not found",
            )

        existing = user_list_repository.get_item(db, profile_id, movie_id, list_type=list_type)
        if existing:
            return WatchlistActionResponse(
                status="added",
                profile_id=profile_id,
                movie_id=movie_id,
                message="Movie is already in watchlist",
            )

        user_list_repository.add_item(db, profile_id, movie_id, list_type=list_type)
        return WatchlistActionResponse(
            status="added",
            profile_id=profile_id,
            movie_id=movie_id,
            message="Movie successfully added to watchlist",
        )

    def remove_from_watchlist(
        self, db: Session, profile_id: str, movie_id: int, list_type: str = "watchlist"
    ) -> WatchlistActionResponse:
        """Remove movie from user's watchlist.
        
        Raises 404 if profile or movie does not exist.
        """
        profile = profile_repository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found",
            )

        movie = movie_repository.get_by_id(db, movie_id)
        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with ID {movie_id} not found",
            )

        removed = user_list_repository.remove_item(db, profile_id, movie_id, list_type=list_type)
        return WatchlistActionResponse(
            status="removed",
            profile_id=profile_id,
            movie_id=movie_id,
            message="Movie removed from watchlist" if removed else "Movie was not in watchlist",
        )

    def is_in_watchlist(
        self, db: Session, profile_id: str, movie_id: int, list_type: str = "watchlist"
    ) -> bool:
        """Check if movie is saved in profile's watchlist."""
        return user_list_repository.is_in_list(db, profile_id, movie_id, list_type=list_type)


watchlist_service = WatchlistService()
