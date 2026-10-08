from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.movie import Movie
from app.repositories.movie_repository import movie_repository


class MovieService:
    """Service managing movie metadata retrieval and catalog exploration."""

    def get_movie(self, db: Session, movie_id: int) -> Optional[Movie]:
        return movie_repository.get_by_id(db, movie_id)

    def search_movies(self, db: Session, query: str, limit: int = 30) -> List[Movie]:
        if not query or not query.strip():
            return []
        return movie_repository.search(db, query.strip(), limit=limit)

    def get_starter_grid(self, db: Session, limit: int = 24) -> List[Movie]:
        return movie_repository.get_starter_grid(db, limit=limit)


movie_service = MovieService()
