from typing import List, Optional, Sequence
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.models.movie import Movie


class MovieRepository:
    """Repository handling Movie database queries."""

    def get_by_id(self, db: Session, movie_id: int) -> Optional[Movie]:
        return db.query(Movie).filter(Movie.id == movie_id).first()

    def get_by_item_idx(self, db: Session, item_idx: int) -> Optional[Movie]:
        return db.query(Movie).filter(Movie.item_idx == item_idx).first()

    def get_by_item_indices(self, db: Session, item_indices: Sequence[int]) -> List[Movie]:
        if not item_indices:
            return []
        movies = db.query(Movie).filter(Movie.item_idx.in_(item_indices)).all()
        # Maintain order of item_indices
        mapping = {m.item_idx: m for m in movies if m.item_idx is not None}
        ordered = [mapping[idx] for idx in item_indices if idx in mapping]
        return ordered

    def search(self, db: Session, query: str, limit: int = 30) -> List[Movie]:
        term = f"%{query.strip()}%"
        return (
            db.query(Movie)
            .filter(
                or_(
                    Movie.title.ilike(term),
                    Movie.title_raw.ilike(term),
                )
            )
            .order_by(Movie.vote_count.desc(), Movie.id.asc())
            .limit(limit)
            .all()
        )

    def get_starter_grid(self, db: Session, limit: int = 24) -> List[Movie]:
        """Fetch popular, diverse titles across genres for onboarding rating."""
        return (
            db.query(Movie)
            .filter(Movie.item_idx.isnot(None))
            .order_by(Movie.vote_count.desc(), Movie.id.asc())
            .limit(limit)
            .all()
        )

    def get_by_genre(self, db: Session, genre: str, limit: int = 20) -> List[Movie]:
        """Fetch top movies containing a given genre string."""
        from sqlalchemy import cast, String
        return (
            db.query(Movie)
            .filter(cast(Movie.genres, String).ilike(f"%{genre}%"))
            .order_by(Movie.vote_count.desc())
            .limit(limit)
            .all()
        )


movie_repository = MovieRepository()
