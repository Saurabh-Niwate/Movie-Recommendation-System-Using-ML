"""Item-based Collaborative Filtering using KNN with Adjusted Cosine Similarity.

Replicates the core algorithm of:
Furtado & Singh (2020), 'Movie recommendation system using machine learning',
International Journal of Research in Industrial Engineering, 9(1), 84-98.
"""
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import scipy.sparse as sp
from recsys.models.base import Recommender


class ItemKNN(Recommender):
    """Item-based KNN Recommender using Adjusted Cosine Similarity."""

    name: str = "item_knn"

    def __init__(
        self,
        k: int = 40,
        shrink: float = 50.0,
        min_sim: float = 0.0,
        damping: float = 25.0,
    ):
        super().__init__()
        self.k = k
        self.shrink = shrink
        self.min_sim = min_sim
        self.damping = damping

        self.S: np.ndarray = np.array([[]], dtype=np.float32)  # item-item similarity matrix
        self.co_counts: np.ndarray = np.array([[]], dtype=np.int32)
        self.item_biases: np.ndarray = np.array([], dtype=np.float32)

    def fit(self, R: sp.csr_matrix) -> "ItemKNN":
        """Compute item-item adjusted cosine similarity matrix.
        
        Args:
            R: User-item rating CSR matrix of shape (n_users, n_items).
        """
        R = R.astype(np.float32).tocsr()
        self.n_users, self.n_items = R.shape
        self.global_mean = float(R.data.mean()) if R.nnz > 0 else 3.5

        # Calculate per-user average ratings
        user_counts = np.diff(R.indptr)
        user_sums = np.asarray(R.sum(axis=1)).ravel()
        user_means = np.zeros(self.n_users, dtype=np.float32)
        valid_users = user_counts > 0
        user_means[valid_users] = user_sums[valid_users] / user_counts[valid_users]

        # Centered rating matrix Rc: r_ui - r_bar_u
        Rc = R.copy()
        Rc.data -= np.repeat(user_means, user_counts)

        # Numerator: Rc.T @ Rc computes sum over co-raters of (r_ui - r_bar_u)(r_uj - r_bar_u)
        num = (Rc.T @ Rc).toarray().astype(np.float32)

        # Denominator norms: sqrt(sum (r_ui - r_bar_u)^2)
        norms = np.sqrt(np.asarray(Rc.multiply(Rc).sum(axis=0)).ravel().astype(np.float32)) + 1e-9
        S = num / np.outer(norms, norms)

        # Co-occurrence counts
        B = R.copy()
        B.data[:] = 1.0
        co_counts = (B.T @ B).toarray().astype(np.int32)

        # Significance shrinkage: penalize similarities based on small numbers of co-raters
        if self.shrink > 0:
            shrink_weights = co_counts / (co_counts + self.shrink)
            S *= shrink_weights

        # Zero out self-similarity and filter negative or small similarities
        np.fill_diagonal(S, 0.0)
        S[S < self.min_sim] = 0.0

        self.S = S.astype(np.float32)
        self.co_counts = co_counts

        # Fit fallback item biases: b_i = (sum(r_ui - mu)) / (count + damping)
        R_csc = R.tocsc()
        item_counts = np.diff(R_csc.indptr)
        item_sums = np.asarray(R_csc.sum(axis=0)).ravel()
        self.item_biases = ((item_sums - item_counts * self.global_mean) / (item_counts + self.damping)).astype(np.float32)

        return self

    def predict(self, user_vec: sp.csr_matrix, items: np.ndarray, user_idx: Optional[int] = None) -> np.ndarray:
        """Predict ratings for user on candidate items using Paper's Eq. §1.1.3:
        
        r_hat_ui = r_bar_u + sum_{j in N_k(i; u)} sim(i, j) * (r_uj - r_bar_u) / sum_{j in N_k(i; u)} |sim(i, j)|
        """
        items_arr = np.asarray(items, dtype=np.int32)
        if len(items_arr) == 0:
            return np.array([], dtype=np.float32)

        if user_vec.nnz == 0:
            # Fallback to global mean + item bias
            return np.clip(self.global_mean + self.item_biases[items_arr], 1.0, 5.0)

        rated_indices = user_vec.indices
        rated_values = user_vec.data.astype(np.float32)
        user_mean = float(np.mean(rated_values))
        deviations = rated_values - user_mean

        # Extract similarities between target items and user's rated items: shape (len(items), len(rated_indices))
        item_sims = self.S[np.ix_(items_arr, rated_indices)].copy()

        # Keep top-k neighbors for each target item
        if item_sims.shape[1] > self.k:
            # Find k-th largest value threshold per row
            threshold = -np.partition(-item_sims, self.k - 1, axis=1)[:, self.k - 1:self.k]
            item_sims[item_sims < threshold] = 0.0

        # Mask non-positive similarities
        item_sims[item_sims <= 0.0] = 0.0

        denom = np.sum(item_sims, axis=1)
        numer = item_sims @ deviations

        # Prediction computation
        valid_mask = denom > 1e-9
        preds = np.zeros(len(items_arr), dtype=np.float32)

        preds[valid_mask] = user_mean + numer[valid_mask] / denom[valid_mask]
        # Fallback for items with no similarity to any of user's rated items
        preds[~valid_mask] = user_mean + self.item_biases[items_arr[~valid_mask]]

        return np.clip(preds, 1.0, 5.0)

    def score_all(self, user_vec: sp.csr_matrix, user_idx: Optional[int] = None) -> np.ndarray:
        """Return ranking scores for all items in [0 .. n_items - 1].
        
        When significance shrinkage is enabled, applies neighbor support damping
        to avoid ranking low-support obscure items at the top.
        """
        if user_vec.nnz == 0:
            return np.clip(self.global_mean + self.item_biases, 1.0, 5.0)

        rated_indices = user_vec.indices
        rated_values = user_vec.data.astype(np.float32)
        user_mean = float(np.mean(rated_values))
        deviations = rated_values - user_mean

        sims = self.S[:, rated_indices].copy()
        sims[sims <= 0.0] = 0.0
        denom = np.sum(sims, axis=1)
        numer = sims @ deviations

        # Damping parameter: active only when significance shrinkage is enabled (> 0)
        damping = 1.5 if self.shrink > 0.0 else 0.0
        valid_mask = denom > 1e-9
        scores = np.zeros(self.n_items, dtype=np.float32)

        scores[valid_mask] = user_mean + numer[valid_mask] / (denom[valid_mask] + damping)
        scores[~valid_mask] = user_mean + self.item_biases[~valid_mask]

        return scores.astype(np.float32)

    def similar_items(self, item_idx: int, n: int = 10) -> List[Tuple[int, float]]:
        """Return the n most similar items to item_idx for 'More like this'."""
        if item_idx < 0 or item_idx >= self.n_items:
            return []
        sims = self.S[item_idx].copy()
        top_indices = np.argpartition(-sims, min(n, len(sims)) - 1)[:n]
        top_indices = top_indices[np.argsort(-sims[top_indices])]
        return [(int(idx), float(sims[idx])) for idx in top_indices if sims[idx] > 0]

    def explain(self, user_vec: sp.csr_matrix, item_idx: int, top_n: int = 3) -> List[Dict[str, Any]]:
        """Explain recommendation: identify user's rated items that contributed most to score."""
        if user_vec.nnz == 0 or item_idx < 0 or item_idx >= self.n_items:
            return []
        rated_indices = user_vec.indices
        rated_values = user_vec.data
        user_mean = float(np.mean(rated_values))

        sims = self.S[item_idx, rated_indices]
        contributions = sims * (rated_values - user_mean)

        top_k = np.argsort(-contributions)[:top_n]
        explanations = []
        for idx in top_k:
            if sims[idx] > 0:
                explanations.append({
                    "neighbor_item_idx": int(rated_indices[idx]),
                    "similarity": float(sims[idx]),
                    "user_rating": float(rated_values[idx]),
                    "contribution": float(contributions[idx]),
                })
        return explanations

    def save(self, path: Path) -> None:
        """Save sparse/compressed representation of similarity matrix to .npz."""
        path.parent.mkdir(parents=True, exist_ok=True)
        # Store top-100 neighbors per item to save space and speed up loading
        n_neighbors = min(100, self.n_items)
        sparse_S = sp.lil_matrix((self.n_items, self.n_items), dtype=np.float32)
        for i in range(self.n_items):
            row = self.S[i]
            if np.any(row > 0):
                top_idx = np.argpartition(-row, min(n_neighbors, len(row)) - 1)[:n_neighbors]
                sparse_S[i, top_idx] = row[top_idx]

        sp.save_npz(
            path,
            sparse_S.tocsr(),
        )
        # Save companion metadata
        meta_path = path.with_suffix(".json")
        meta = {
            "name": self.name,
            "k": self.k,
            "shrink": self.shrink,
            "min_sim": self.min_sim,
            "damping": self.damping,
            "n_users": self.n_users,
            "n_items": self.n_items,
            "global_mean": self.global_mean,
            "item_biases": self.item_biases.tolist(),
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            import json
            json.dump(meta, f)

    @classmethod
    def load(cls, path: Path) -> "ItemKNN":
        """Load ItemKNN model from .npz and .json."""
        import json
        meta_path = path.with_suffix(".json")
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        model = cls(
            k=meta.get("k", 40),
            shrink=meta.get("shrink", 50.0),
            min_sim=meta.get("min_sim", 0.0),
            damping=meta.get("damping", 25.0),
        )
        model.n_users = meta["n_users"]
        model.n_items = meta["n_items"]
        model.global_mean = meta["global_mean"]
        model.item_biases = np.array(meta["item_biases"], dtype=np.float32)

        sparse_S = sp.load_npz(path).toarray().astype(np.float32)
        model.S = sparse_S
        return model
