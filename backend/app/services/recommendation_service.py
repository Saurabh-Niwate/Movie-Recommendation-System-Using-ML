from typing import List, Dict, Any, Optional
import numpy as np
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.movie import Movie
from app.models.rating import Rating
from app.schemas.movie import MovieSummary
from app.schemas.recommendation import (
    RecommendationItem,
    BecauseYouLikedResponse,
    AlsoWatchedItem,
    GenreCarousel,
)
from app.repositories.profile_repository import profile_repository
from app.repositories.movie_repository import movie_repository
from app.repositories.rating_repository import rating_repository
from app.infra.model_registry import get_model_registry
from app.services.cache import get_cache_service


class RecommendationService:
    """Service providing personalized top picks, billboard, neighborhood, and association recommendations."""

    def _check_cold_start_gating(self, profile: Profile) -> None:
        """Enforce strict cold-start gating: profiles with <6 ratings cannot access collaborative filtering."""
        if (profile.id == "mukesh" and profile.ratings_count < 6) or (profile.is_cold_start and profile.ratings_count < 6):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cold start profile requires at least 6 ratings",
            )

    def _build_recommendation_item(
        self, movie: Movie, score: float, algorithm: str
    ) -> RecommendationItem:
        """Construct a standardized RecommendationItem from Movie entity and numerical score."""
        # Scale score in [1.0, 5.0] to a Netflix-style Match Percentage [50%, 99%]
        match_pct = int(np.clip((score / 5.0) * 100.0, 50.0, 99.0))
        return RecommendationItem(
            id=movie.id,
            movie_lens_id=movie.movie_lens_id,
            title=movie.title,
            year=movie.year,
            genres=movie.genres or [],
            poster_path=movie.poster_path,
            backdrop_path=movie.backdrop_path,
            synopsis=movie.synopsis,
            overview=movie.overview,
            vote_average=movie.vote_average,
            score=round(float(score), 4),
            match_percent=match_pct,
            algorithm=algorithm,
            item_idx=movie.item_idx,
        )

    def get_recommendations(
        self,
        db: Session,
        profile_id: str,
        model_name: str = "funk_svd",
        limit: int = 20,
    ) -> List[RecommendationItem]:
        """Generate personalized Top Picks for a profile using either Funk-SVD or Item-KNN."""
        profile = profile_repository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found",
            )

        self._check_cold_start_gating(profile)

        # Check in-memory TTLCache
        cache = get_cache_service()
        cache_key = f"{profile_id}:{model_name}:top_picks:{limit}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        reg = get_model_registry()
        user_ratings_dict = rating_repository.get_user_ratings_dict(db, profile.id)
        user_vec = reg.build_user_csr(user_ratings_dict)

        model_key = model_name.lower().strip()
        if model_key in {"item_knn", "knn"} and reg.item_knn is not None:
            raw_scores = reg.item_knn.score_all(user_vec)
            algo_label = "Item-KNN"
        else:
            if reg.funk_svd is None:
                raise HTTPException(status_code=500, detail="FunkSVD model not loaded")
            raw_scores = reg.funk_svd.score_all(user_vec)
            algo_label = "Funk-SVD"

        # Exclude items the user has already rated
        scores = raw_scores.copy()
        for rated_item_idx in user_ratings_dict.keys():
            if 0 <= rated_item_idx < len(scores):
                scores[rated_item_idx] = -1e9

        # Extract top-K candidate item indices
        top_k = min(limit * 2, len(scores))
        top_indices = np.argpartition(-scores, top_k - 1)[:top_k]
        top_indices = top_indices[np.argsort(-scores[top_indices])]

        # Fetch corresponding movies from DB
        candidate_movies = movie_repository.get_by_item_indices(db, top_indices.tolist())
        items: List[RecommendationItem] = []
        for m in candidate_movies:
            if m.item_idx is not None and m.item_idx < len(scores):
                sc = scores[m.item_idx]
                if sc > -1e8:
                    items.append(self._build_recommendation_item(m, sc, algo_label))
            if len(items) >= limit:
                break

        # Save to TTLCache
        cache.set(cache_key, items, profile_id=profile.id)
        return items

    def get_billboard(self, db: Session, profile_id: str) -> RecommendationItem:
        """Fetch the hero billboard movie recommendation for the active profile."""
        profile = profile_repository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found",
            )

        self._check_cold_start_gating(profile)

        cache = get_cache_service()
        cache_key = f"{profile_id}:billboard"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        top_recs = self.get_recommendations(db, profile_id=profile.id, model_name="funk_svd", limit=5)
        if not top_recs:
            # Fallback to catalog movie
            fallback = movie_repository.get_starter_grid(db, limit=1)
            if not fallback:
                raise HTTPException(status_code=404, detail="No movies available for billboard")
            item = self._build_recommendation_item(fallback[0], 4.8, "Catalog Featured")
        else:
            item = top_recs[0]

        cache.set(cache_key, item, profile_id=profile.id)
        return item

    def get_because_you_liked(self, db: Session, profile_id: str) -> BecauseYouLikedResponse:
        """Generate 'Because you liked [Movie]' row using Item-KNN adjusted cosine neighbors."""
        profile = profile_repository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found",
            )

        self._check_cold_start_gating(profile)

        cache = get_cache_service()
        cache_key = f"{profile_id}:because_you_liked"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Find profile's top-rated movie
        user_ratings = rating_repository.get_user_ratings(db, profile.id)
        if not user_ratings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No rated movies found for this profile",
            )

        # Sort by rating desc
        valid_ratings = [r for r in user_ratings if r.item_idx is not None]
        if not valid_ratings:
            raise HTTPException(status_code=404, detail="No valid rated items found")

        valid_ratings.sort(key=lambda r: (r.rating, r.id), reverse=True)
        top_rating = valid_ratings[0]
        source_movie = movie_repository.get_by_id(db, top_rating.movie_id)
        if not source_movie or source_movie.item_idx is None:
            raise HTTPException(status_code=404, detail="Source movie not found")

        reg = get_model_registry()
        if reg.item_knn is None:
            raise HTTPException(status_code=500, detail="ItemKNN model not loaded")

        # Find adjusted cosine neighbors
        similar_items = reg.item_knn.similar_items(source_movie.item_idx, n=15)
        neighbor_indices = [idx for idx, _ in similar_items]
        sim_scores_map = {idx: sim for idx, sim in similar_items}

        # Filter out movies already rated
        rated_set = {r.item_idx for r in valid_ratings}
        filtered_indices = [idx for idx in neighbor_indices if idx not in rated_set]

        similar_movies = movie_repository.get_by_item_indices(db, filtered_indices)
        recs: List[RecommendationItem] = []
        for m in similar_movies:
            if m.item_idx is not None:
                sim_val = sim_scores_map.get(m.item_idx, 0.5)
                # Map similarity [0, 1] to predicted score ~ [3.0, 5.0]
                pred_score = 3.0 + sim_val * 2.0
                recs.append(self._build_recommendation_item(m, pred_score, "Item-KNN Similarity"))
            if len(recs) >= 10:
                break

        response = BecauseYouLikedResponse(
            source_movie=MovieSummary.model_validate(source_movie),
            recommendations=recs,
        )
        cache.set(cache_key, response, profile_id=profile.id)
        return response

    def get_also_watched(self, db: Session, movie_id: int, limit: int = 10) -> List[AlsoWatchedItem]:
        """Generate 'Users also watched' recommendations using Association Rules co-occurrence Lift."""
        movie = movie_repository.get_by_id(db, movie_id)
        if not movie or movie.item_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with ID {movie_id} not found",
            )

        reg = get_model_registry()
        if reg.associations is None:
            raise HTTPException(status_code=500, detail="AssociationRules model not loaded")

        raw_associations = reg.associations.get_also_watched(movie.item_idx, k=limit)
        if not raw_associations:
            return []

        item_indices = [a["item_idx"] for a in raw_associations]
        assoc_info = {a["item_idx"]: a for a in raw_associations}

        assoc_movies = movie_repository.get_by_item_indices(db, item_indices)
        result: List[AlsoWatchedItem] = []
        for m in assoc_movies:
            if m.item_idx in assoc_info:
                info = assoc_info[m.item_idx]
                result.append(
                    AlsoWatchedItem(
                        id=m.id,
                        title=m.title,
                        genres=m.genres or [],
                        poster_path=m.poster_path,
                        backdrop_path=m.backdrop_path,
                        lift=float(info["lift"]),
                        cooccurrence=int(info["cooccurrence"]),
                    )
                )
        return result

    def get_genre_carousels(self, db: Session, profile_id: Optional[str] = None) -> List[GenreCarousel]:
        """Generate diverse genre carousels for the browse page."""
        genres = ["Action", "Sci-Fi", "Drama", "Romance", "Comedy", "Thriller"]
        carousels: List[GenreCarousel] = []

        for g in genres:
            movies = movie_repository.get_by_genre(db, g, limit=12)
            items = [
                self._build_recommendation_item(m, m.vote_average or 4.0, f"Genre: {g}")
                for m in movies
            ]
            carousels.append(GenreCarousel(genre=g, movies=items))

        return carousels


recommendation_service = RecommendationService()
