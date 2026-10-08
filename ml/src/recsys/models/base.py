"""Abstract base class for all recommenders."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import scipy.sparse as sp


class Recommender(ABC):
    """Common interface for recommendation algorithms."""

    name: str = "base"

    def __init__(self):
        self.n_items: int = 0
        self.n_users: int = 0
        self.global_mean: float = 3.5

    @abstractmethod
    def fit(self, R: sp.csr_matrix) -> "Recommender":
        """Fit the model on user-item rating CSR matrix."""
        pass

    @abstractmethod
    def predict(self, user_vec: sp.csr_matrix, items: np.ndarray, user_idx: Optional[int] = None) -> np.ndarray:
        """Predict ratings for a user on given item indices.
        
        Args:
            user_vec: 1 x n_items sparse CSR matrix of user's ratings.
            items: 1D array of item indices to predict.
            user_idx: Optional integer index of user if known in-sample.
        
        Returns:
            1D array of predicted ratings in [1.0, 5.0].
        """
        pass

    def score_all(self, user_vec: sp.csr_matrix, user_idx: Optional[int] = None) -> np.ndarray:
        """Return ranking scores for all items in [0 .. n_items - 1]."""
        items = np.arange(self.n_items, dtype=np.int32)
        return self.predict(user_vec, items, user_idx=user_idx)

    def recommend(
        self,
        user_vec: sp.csr_matrix,
        k: int = 10,
        exclude_seen: bool = True,
        candidates: Optional[np.ndarray] = None,
        user_idx: Optional[int] = None,
    ) -> List[Tuple[int, float]]:
        """Generate top-k recommendations for a given user rating vector.
        
        Args:
            user_vec: 1 x n_items sparse CSR matrix.
            k: Number of recommendations.
            exclude_seen: Whether to exclude already rated items.
            candidates: Optional subset of candidate item indices.
            user_idx: Optional integer user index if known.
        
        Returns:
            List of (item_idx, score) sorted descending by score.
        """
        scores = self.score_all(user_vec, user_idx=user_idx).copy()

        if exclude_seen and user_vec.nnz > 0:
            seen_indices = user_vec.indices
            scores[seen_indices] = -np.inf

        if candidates is not None:
            cand_mask = np.full(self.n_items, -np.inf, dtype=np.float32)
            cand_mask[candidates] = 0.0
            scores += cand_mask

        # Top-k selection
        valid_count = np.sum(np.isfinite(scores))
        k_actual = min(k, int(valid_count))
        if k_actual == 0:
            return []

        top_indices = np.argpartition(-scores, k_actual - 1)[:k_actual]
        # Sort top indices
        top_indices = top_indices[np.argsort(-scores[top_indices])]

        return [(int(idx), float(scores[idx])) for idx in top_indices]

    @abstractmethod
    def save(self, path: Path) -> None:
        """Save model artifacts to disk."""
        pass

    @classmethod
    @abstractmethod
    def load(cls, path: Path) -> "Recommender":
        """Load model artifacts from disk."""
        pass
