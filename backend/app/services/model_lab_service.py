from typing import Dict, Any, List, Optional, Union
import numpy as np
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.movie import Movie
from app.schemas.model_lab import (
    ConvergenceResponse,
    SideBySideCompareResponse,
    CompareItem,
    FunkSVDExplainResponse,
    ItemKNNExplainResponse,
    LatentFactor,
    NeighborContribution,
)
from app.repositories.profile_repository import profile_repository
from app.repositories.movie_repository import movie_repository
from app.repositories.rating_repository import rating_repository
from app.infra.model_registry import get_model_registry


class ModelLabService:
    """Service providing leaderboard metrics, convergence curves, model comparisons, and mathematical explanations."""

    def get_leaderboard(self) -> Dict[str, Any]:
        """Fetch model evaluation benchmark metrics from artifacts/v1/metrics.json."""
        reg = get_model_registry()
        if not reg.metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation metrics artifact not available",
            )
        return reg.metrics

    def get_convergence(self) -> ConvergenceResponse:
        """Fetch Funk-SVD training loss and validation RMSE history across epochs."""
        reg = get_model_registry()
        conv_data = reg.convergence
        if not conv_data:
            # Fallback to funk_svd metadata if convergence.json was not loaded separately
            if reg.funk_svd and reg.funk_svd.convergence_history:
                conv_data = {
                    "epochs": reg.funk_svd.convergence_history,
                    "best_epoch": int(np.argmin([e["val_rmse"] for e in reg.funk_svd.convergence_history]) + 1),
                    "training_time_sec": 2.65,
                    "algorithm": "Funk-SVD",
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Convergence history not available",
                )

        return ConvergenceResponse(
            algorithm=conv_data.get("algorithm", "Funk-SVD"),
            best_epoch=conv_data.get("best_epoch", 1),
            training_time_sec=float(conv_data.get("training_time_sec", 2.65)),
            epochs=conv_data.get("epochs", []),
        )

    def compare_models(
        self, db: Session, profile_id: str, limit: int = 10
    ) -> SideBySideCompareResponse:
        """Generate side-by-side Top-10 recommendations comparing Item-KNN and Funk-SVD."""
        profile = profile_repository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found",
            )

        reg = get_model_registry()
        if reg.funk_svd is None or reg.item_knn is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Recommender models are not loaded in registry",
            )

        user_ratings_dict = rating_repository.get_user_ratings_dict(db, profile.id)
        user_vec = reg.build_user_csr(user_ratings_dict)

        # 1. Funk-SVD scores
        svd_scores = reg.funk_svd.score_all(user_vec)
        # 2. Item-KNN scores
        knn_scores = reg.item_knn.score_all(user_vec)

        # Mask already rated items
        for r_idx in user_ratings_dict.keys():
            if 0 <= r_idx < len(svd_scores):
                svd_scores[r_idx] = -1e9
            if 0 <= r_idx < len(knn_scores):
                knn_scores[r_idx] = -1e9

        def get_top_items(scores_arr: np.ndarray) -> List[CompareItem]:
            top_k = min(limit * 2, len(scores_arr))
            top_indices = np.argpartition(-scores_arr, top_k - 1)[:top_k]
            top_indices = top_indices[np.argsort(-scores_arr[top_indices])]

            candidate_movies = movie_repository.get_by_item_indices(db, top_indices.tolist())
            items: List[CompareItem] = []
            for m in candidate_movies:
                if m.item_idx is not None and m.item_idx < len(scores_arr):
                    sc = scores_arr[m.item_idx]
                    if sc > -1e8:
                        match_pct = int(np.clip((sc / 5.0) * 100.0, 50.0, 99.0))
                        items.append(
                            CompareItem(
                                movie_id=m.id,
                                title=m.title,
                                genres=m.genres or [],
                                poster_path=m.poster_path,
                                backdrop_path=m.backdrop_path,
                                score=round(float(sc), 4),
                                match_percent=match_pct,
                            )
                        )
                if len(items) >= limit:
                    break
            return items

        funk_svd_items = get_top_items(svd_scores)
        item_knn_items = get_top_items(knn_scores)

        return SideBySideCompareResponse(
            profile_id=profile.id,
            item_knn=item_knn_items,
            funk_svd=funk_svd_items,
        )

    def explain_prediction(
        self,
        db: Session,
        profile_id: str,
        movie_id: int,
        model_name: str = "funk_svd",
    ) -> Union[FunkSVDExplainResponse, ItemKNNExplainResponse]:
        """Generate mathematical breakdown of predicted score for Funk-SVD or Item-KNN."""
        profile = profile_repository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found",
            )

        movie = movie_repository.get_by_id(db, movie_id)
        if not movie or movie.item_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with ID {movie_id} not found or unindexed",
            )

        reg = get_model_registry()
        user_ratings_dict = rating_repository.get_user_ratings_dict(db, profile.id)
        user_vec = reg.build_user_csr(user_ratings_dict)

        model_key = model_name.lower().strip()
        if model_key in {"item_knn", "knn"}:
            if reg.item_knn is None:
                raise HTTPException(status_code=500, detail="ItemKNN model not loaded")

            raw_neighbors = reg.item_knn.explain(user_vec, movie.item_idx, top_n=5)
            # Predict overall score
            pred_arr = reg.item_knn.predict(user_vec, np.array([movie.item_idx]))
            pred_score = float(pred_arr[0]) if len(pred_arr) > 0 else reg.item_knn.global_mean

            user_mean = (
                float(np.mean(list(user_ratings_dict.values())))
                if user_ratings_dict
                else reg.item_knn.global_mean
            )

            # Resolve neighbor movie metadata
            neighbor_item_indices = [n["neighbor_item_idx"] for n in raw_neighbors]
            neighbor_movies = movie_repository.get_by_item_indices(db, neighbor_item_indices)
            movie_map = {m.item_idx: m for m in neighbor_movies if m.item_idx is not None}

            neighbor_contributions: List[NeighborContribution] = []
            for n in raw_neighbors:
                n_idx = n["neighbor_item_idx"]
                m_obj = movie_map.get(n_idx)
                m_id = m_obj.id if m_obj else reg.item_idx_to_movie_id.get(n_idx, n_idx)
                m_title = m_obj.title if m_obj else f"Movie {m_id}"

                neighbor_contributions.append(
                    NeighborContribution(
                        movie_id=m_id,
                        item_idx=n_idx,
                        title=m_title,
                        similarity=round(float(n["similarity"]), 4),
                        user_rating=round(float(n["user_rating"]), 2),
                        contribution=round(float(n["contribution"]), 4),
                    )
                )

            match_pct = int(np.clip((pred_score / 5.0) * 100.0, 50.0, 99.0))
            return ItemKNNExplainResponse(
                model="item_knn",
                profile_id=profile.id,
                movie_id=movie.id,
                title=movie.title,
                user_mean=round(user_mean, 4),
                neighbors=neighbor_contributions,
                predicted_score=round(pred_score, 4),
                match_percent=match_pct,
            )

        # Default: Funk-SVD explainability
        if reg.funk_svd is None:
            raise HTTPException(status_code=500, detail="FunkSVD model not loaded")

        raw_svd = reg.funk_svd.explain(user_vec, movie.item_idx)
        latent_factors = [
            LatentFactor(
                factor_index=f["factor_index"],
                user_val=round(float(f["user_val"]), 4),
                item_val=round(float(f["item_val"]), 4),
                product=round(float(f["product"]), 4),
            )
            for f in raw_svd.get("latent_breakdown", [])
        ]

        pred_score = float(raw_svd["predicted_score"])
        match_pct = int(np.clip((pred_score / 5.0) * 100.0, 50.0, 99.0))

        return FunkSVDExplainResponse(
            model="funk_svd",
            profile_id=profile.id,
            movie_id=movie.id,
            title=movie.title,
            mu=round(float(raw_svd["mu"]), 4),
            user_bias=round(float(raw_svd["user_bias"]), 4),
            item_bias=round(float(raw_svd["item_bias"]), 4),
            dot_product=round(float(raw_svd["dot_product"]), 4),
            latent_breakdown=latent_factors,
            predicted_score=round(pred_score, 4),
            match_percent=match_pct,
        )


model_lab_service = ModelLabService()
