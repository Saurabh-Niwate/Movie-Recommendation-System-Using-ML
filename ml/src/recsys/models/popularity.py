"""Popularity and Bayesian average baseline recommender."""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import scipy.sparse as sp
from recsys.models.base import Recommender


class PopularityRecommender(Recommender):
    """Bayesian weighted average baseline recommender."""

    name: str = "popularity"

    def __init__(self, quantile: float = 0.75, damping: float = 25.0):
        super().__init__()
        self.quantile = quantile
        self.damping = damping
        self.item_counts: np.ndarray = np.array([], dtype=np.int32)
        self.item_means: np.ndarray = np.array([], dtype=np.float32)
        self.weighted_ratings: np.ndarray = np.array([], dtype=np.float32)
        self.item_biases: np.ndarray = np.array([], dtype=np.float32)

    def fit(self, R: sp.csr_matrix) -> "PopularityRecommender":
        """Compute item statistics and Bayesian weighted ratings."""
        self.n_users, self.n_items = R.shape
        self.global_mean = float(R.data.mean()) if R.nnz > 0 else 3.5

        # Compute counts and sums per column
        R_csc = R.tocsc()
        counts = np.diff(R_csc.indptr).astype(np.int32)
        sums = np.asarray(R_csc.sum(axis=0)).ravel().astype(np.float32)

        means = np.zeros(self.n_items, dtype=np.float32)
        mask = counts > 0
        means[mask] = sums[mask] / counts[mask]
        means[~mask] = self.global_mean

        # m threshold based on quantile of counts of rated movies
        rated_counts = counts[counts > 0]
        m = float(np.quantile(rated_counts, self.quantile)) if len(rated_counts) > 0 else 10.0
        m = max(m, 5.0)

        # Bayesian weighted rating formula:
        # WR = (v / (v + m)) * R_bar + (m / (v + m)) * C
        wr = (counts / (counts + m)) * means + (m / (counts + m)) * self.global_mean

        # Regularized item bias for rating prediction: b_i = (sum - count * mu) / (count + damping)
        biases = (sums - counts * self.global_mean) / (counts + self.damping)

        self.item_counts = counts
        self.item_means = means
        self.weighted_ratings = wr.astype(np.float32)
        self.item_biases = biases.astype(np.float32)
        return self

    def predict(self, user_vec: sp.csr_matrix, items: np.ndarray, user_idx: Optional[int] = None) -> np.ndarray:
        """Baseline rating prediction: r_hat = mu + b_i."""
        preds = self.global_mean + self.item_biases[items]
        return np.clip(preds, 1.0, 5.0)

    def score_all(self, user_vec: sp.csr_matrix, user_idx: Optional[int] = None) -> np.ndarray:
        """Return Bayesian weighted ratings for all items."""
        return self.weighted_ratings.copy()

    def save(self, path: Path) -> None:
        """Save popularity statistics to JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "name": self.name,
            "n_users": self.n_users,
            "n_items": self.n_items,
            "global_mean": self.global_mean,
            "quantile": self.quantile,
            "damping": self.damping,
            "weighted_ratings": self.weighted_ratings.tolist(),
            "item_biases": self.item_biases.tolist(),
            "item_counts": self.item_counts.tolist(),
            "item_means": self.item_means.tolist(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    @classmethod
    def load(cls, path: Path) -> "PopularityRecommender":
        """Load popularity statistics from JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        model = cls(quantile=data.get("quantile", 0.75), damping=data.get("damping", 25.0))
        model.n_users = data["n_users"]
        model.n_items = data["n_items"]
        model.global_mean = data["global_mean"]
        model.weighted_ratings = np.array(data["weighted_ratings"], dtype=np.float32)
        model.item_biases = np.array(data["item_biases"], dtype=np.float32)
        model.item_counts = np.array(data["item_counts"], dtype=np.int32)
        model.item_means = np.array(data["item_means"], dtype=np.float32)
        return model
