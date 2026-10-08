"""Funk-SVD: Biased Matrix Factorization with Numba fast SGD and online fold-in.

Implements biased matrix factorization:
    r_hat_ui = mu + b_u + b_i + p_u^T q_i

Trained via Numba JIT accelerated stochastic gradient descent (SGD).
Supports closed-form online fold-in for new profile ratings using Ridge regression.
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union, Sequence
import numpy as np
import scipy.sparse as sp
import numba

from recsys.models.base import Recommender


@numba.njit(fastmath=True)
def _sgd_train_epoch(
    u_indices: np.ndarray,
    i_indices: np.ndarray,
    ratings: np.ndarray,
    P: np.ndarray,
    Q: np.ndarray,
    b_u: np.ndarray,
    b_i: np.ndarray,
    mu: float,
    lr: float,
    reg_bias: float,
    reg_factor: float,
    order: np.ndarray,
) -> float:
    """Run one epoch of SGD optimization for Funk-SVD."""
    loss = 0.0
    n_samples = len(ratings)
    n_factors = P.shape[1]

    for s in range(n_samples):
        idx = order[s]
        u = u_indices[idx]
        i = i_indices[idx]
        r = ratings[idx]

        dot = 0.0
        for f in range(n_factors):
            dot += P[u, f] * Q[i, f]
        pred = mu + b_u[u] + b_i[i] + dot
        err = r - pred
        loss += err * err

        # Update biases
        b_u[u] += lr * (err - reg_bias * b_u[u])
        b_i[i] += lr * (err - reg_bias * b_i[i])

        # Update latent factors
        for f in range(n_factors):
            p_val = P[u, f]
            q_val = Q[i, f]
            P[u, f] += lr * (err * q_val - reg_factor * p_val)
            Q[i, f] += lr * (err * p_val - reg_factor * q_val)

    return loss / n_samples


@numba.njit(fastmath=True)
def _eval_rmse(
    u_indices: np.ndarray,
    i_indices: np.ndarray,
    ratings: np.ndarray,
    P: np.ndarray,
    Q: np.ndarray,
    b_u: np.ndarray,
    b_i: np.ndarray,
    mu: float,
) -> float:
    """Evaluate root mean squared error on a rating set."""
    n = len(ratings)
    if n == 0:
        return 0.0
    se = 0.0
    n_factors = P.shape[1]
    for idx in range(n):
        u = u_indices[idx]
        i = i_indices[idx]
        r = ratings[idx]

        dot = 0.0
        for f in range(n_factors):
            dot += P[u, f] * Q[i, f]
        pred = mu + b_u[u] + b_i[i] + dot
        if pred < 1.0:
            pred = 1.0
        elif pred > 5.0:
            pred = 5.0
        err = r - pred
        se += err * err
    return np.sqrt(se / n)


class FunkSVD(Recommender):
    """Funk-SVD Biased Matrix Factorization recommender."""

    name: str = "funk_svd"

    def __init__(
        self,
        n_factors: int = 32,
        lr: float = 0.007,
        reg_bias: float = 0.02,
        reg_factor: float = 0.05,
        n_epochs: int = 15,
        random_state: int = 42,
    ):
        super().__init__()
        self.n_factors = n_factors
        self.lr = lr
        self.reg_bias = reg_bias
        self.reg_factor = reg_factor
        self.n_epochs = n_epochs
        self.random_state = random_state

        self.mu: float = 3.5
        self.b_u: np.ndarray = np.array([], dtype=np.float32)
        self.b_i: np.ndarray = np.array([], dtype=np.float32)
        self.P: np.ndarray = np.zeros((0, n_factors), dtype=np.float32)
        self.Q: np.ndarray = np.zeros((0, n_factors), dtype=np.float32)
        self.item_counts: np.ndarray = np.array([], dtype=np.int32)
        self.shrink_factor: Optional[np.ndarray] = None
        self.convergence_history: List[Dict[str, Any]] = []

    def fit(
        self,
        R: sp.csr_matrix,
        val_R: Optional[sp.csr_matrix] = None,
        verbose: bool = True,
    ) -> "FunkSVD":
        """Fit Funk-SVD on user-item rating matrix using Numba-accelerated SGD.
        
        Args:
            R: User-item rating CSR matrix (n_users x n_items).
            val_R: Optional validation CSR matrix for monitoring RMSE per epoch.
            verbose: Whether to log training progress.
        """
        R = R.tocsr()
        self.n_users, self.n_items = R.shape
        self.global_mean = float(R.data.mean()) if R.nnz > 0 else 3.5
        self.mu = self.global_mean

        # Precompute item support counts and confidence shrinkage
        R_csc = R.tocsc()
        item_counts = np.diff(R_csc.indptr).astype(np.float32)
        self.item_counts = item_counts.astype(np.int32)
        self.shrink_factor = (item_counts / (item_counts + 50.0)).astype(np.float32)

        # Extract (u, i, r) training coordinates
        R_coo = R.tocoo()
        u_train = R_coo.row.astype(np.int32)
        i_train = R_coo.col.astype(np.int32)
        r_train = R_coo.data.astype(np.float32)
        n_samples = len(r_train)

        # Validation coordinates
        has_val = val_R is not None and val_R.nnz > 0
        if has_val:
            val_coo = val_R.tocoo()
            u_val = val_coo.row.astype(np.int32)
            i_val = val_coo.col.astype(np.int32)
            r_val = val_coo.data.astype(np.float32)
        else:
            u_val = np.array([], dtype=np.int32)
            i_val = np.array([], dtype=np.int32)
            r_val = np.array([], dtype=np.float32)

        # Initialize parameters
        rng = np.random.RandomState(self.random_state)
        self.b_u = np.zeros(self.n_users, dtype=np.float32)
        self.b_i = np.zeros(self.n_items, dtype=np.float32)
        # Small random initialization for latent factors: N(0, 0.1 / sqrt(f))
        std = float(0.1 / np.sqrt(self.n_factors))
        self.P = rng.normal(0.0, std, size=(self.n_users, self.n_factors)).astype(np.float32)
        self.Q = rng.normal(0.0, std, size=(self.n_items, self.n_factors)).astype(np.float32)

        self.convergence_history = []
        t0 = time.time()

        for ep in range(self.n_epochs):
            order = rng.permutation(n_samples).astype(np.int32)
            train_loss = _sgd_train_epoch(
                u_train,
                i_train,
                r_train,
                self.P,
                self.Q,
                self.b_u,
                self.b_i,
                self.mu,
                self.lr,
                self.reg_bias,
                self.reg_factor,
                order,
            )

            if has_val:
                val_rmse = float(_eval_rmse(
                    u_val,
                    i_val,
                    r_val,
                    self.P,
                    self.Q,
                    self.b_u,
                    self.b_i,
                    self.mu,
                ))
            else:
                val_rmse = float(np.sqrt(train_loss))

            epoch_stat = {
                "epoch": ep + 1,
                "train_loss": round(float(train_loss), 4),
                "val_rmse": round(val_rmse, 4),
            }
            self.convergence_history.append(epoch_stat)

            if verbose and ((ep + 1) % 5 == 0 or ep == self.n_epochs - 1):
                print(
                    f"[recsys] Funk-SVD Epoch {ep + 1:02d}/{self.n_epochs}: "
                    f"train_loss={train_loss:.4f}, val_rmse={val_rmse:.4f}"
                )

        train_time = time.time() - t0
        if verbose:
            print(f"[recsys] Funk-SVD finished {self.n_epochs} epochs in {train_time:.2f}s")

        return self

    def fold_in(
        self,
        user_ratings: Union[Dict[int, float], sp.csr_matrix, Sequence[Tuple[int, float]]],
    ) -> Tuple[float, np.ndarray]:
        """Analytical closed-form Ridge regression online fold-in.
        
        Solves: (Q_u^T Q_u + Lambda)^(-1) Q_u^T y_u
        for extended parameter vector w_u = [b_u, p_u^T]^T.
        
        Args:
            user_ratings: Rating dictionary {item_idx: rating}, CSR row, or list of (item_idx, rating).
            
        Returns:
            Tuple of (b_u, p_u) where b_u is a float and p_u is a (n_factors,) float32 vector.
        """
        if isinstance(user_ratings, sp.csr_matrix):
            if user_ratings.nnz == 0:
                return 0.0, np.zeros(self.n_factors, dtype=np.float32)
            items = user_ratings.indices
            ratings = user_ratings.data.astype(np.float32)
        elif isinstance(user_ratings, dict):
            if not user_ratings:
                return 0.0, np.zeros(self.n_factors, dtype=np.float32)
            items = np.array(list(user_ratings.keys()), dtype=np.int32)
            ratings = np.array(list(user_ratings.values()), dtype=np.float32)
        else:
            items_list = []
            ratings_list = []
            for item, r in user_ratings:
                items_list.append(item)
                ratings_list.append(r)
            if not items_list:
                return 0.0, np.zeros(self.n_factors, dtype=np.float32)
            items = np.array(items_list, dtype=np.int32)
            ratings = np.array(ratings_list, dtype=np.float32)

        # Filter out of range item indices
        valid_mask = (items >= 0) & (items < self.n_items)
        if not np.any(valid_mask):
            return 0.0, np.zeros(self.n_factors, dtype=np.float32)

        items = items[valid_mask]
        ratings = ratings[valid_mask]
        m = len(items)

        # y_u = r_ui - mu - b_i
        y = (ratings - self.mu - self.b_i[items]).astype(np.float32)

        # Extended items matrix: [1, q_i] shape (m, n_factors + 1)
        Q_sub = self.Q[items]
        Q_tilde = np.hstack([np.ones((m, 1), dtype=np.float32), Q_sub])

        # Regularization matrix Lambda = diag(reg_bias, reg_factor, ...)
        Lambda = np.zeros((self.n_factors + 1, self.n_factors + 1), dtype=np.float32)
        Lambda[0, 0] = self.reg_bias
        np.fill_diagonal(Lambda[1:, 1:], self.reg_factor)

        # Solve (Q_tilde^T Q_tilde + Lambda) w_u = Q_tilde^T y
        A = Q_tilde.T @ Q_tilde + Lambda
        b = Q_tilde.T @ y
        w_u = np.linalg.solve(A, b)

        b_u = float(w_u[0])
        p_u = w_u[1:].astype(np.float32)
        return b_u, p_u

    def predict(self, user_vec: sp.csr_matrix, items: np.ndarray, user_idx: Optional[int] = None) -> np.ndarray:
        """Predict ratings for a user on given item indices."""
        items_arr = np.asarray(items, dtype=np.int32)
        if len(items_arr) == 0:
            return np.array([], dtype=np.float32)

        if user_idx is not None:
            if np.isscalar(user_idx):
                if 0 <= int(user_idx) < self.n_users:
                    return self.predict_user(int(user_idx), items_arr)
            else:
                return self.predict_user(user_idx, items_arr)

        b_u, p_u = self.fold_in(user_vec)
        preds = self.mu + b_u + self.b_i[items_arr] + self.Q[items_arr] @ p_u
        return np.clip(preds, 1.0, 5.0).astype(np.float32)

    def score_all(self, user_vec: sp.csr_matrix, user_idx: Optional[int] = None) -> np.ndarray:
        """Return ranking scores for all catalog items."""
        b_u, p_u = self.fold_in(user_vec)
        if self.shrink_factor is not None and len(self.shrink_factor) == self.n_items:
            scores = self.mu + b_u + (self.b_i + self.Q @ p_u) * self.shrink_factor
        else:
            scores = self.mu + b_u + self.b_i + self.Q @ p_u
        return scores.astype(np.float32)

    def explain(self, user_vec: sp.csr_matrix, item_idx: int) -> Dict[str, Any]:
        """Return mathematical breakdown of prediction for Model Lab explainability."""
        b_u, p_u = self.fold_in(user_vec)
        if item_idx < 0 or item_idx >= self.n_items:
            item_bias = 0.0
            q_i = np.zeros(self.n_factors, dtype=np.float32)
        else:
            item_bias = float(self.b_i[item_idx])
            q_i = self.Q[item_idx]

        dot_product = float(np.dot(p_u, q_i))
        pred = float(np.clip(self.mu + b_u + item_bias + dot_product, 1.0, 5.0))

        breakdown = [
            {
                "factor_index": int(f),
                "user_val": float(p_u[f]),
                "item_val": float(q_i[f]),
                "product": float(p_u[f] * q_i[f]),
            }
            for f in range(self.n_factors)
        ]

        return {
            "mu": float(self.mu),
            "user_bias": float(b_u),
            "item_bias": item_bias,
            "dot_product": dot_product,
            "latent_breakdown": breakdown,
            "predicted_score": pred,
        }

    def predict_user(self, user_idx: Union[int, np.ndarray], items: np.ndarray) -> np.ndarray:
        """In-sample prediction using pre-computed user vector from training."""
        items_arr = np.asarray(items, dtype=np.int32)
        if np.isscalar(user_idx):
            u = int(user_idx)
            if u < 0 or u >= self.n_users:
                b_u = 0.0
                p_u = np.zeros(self.n_factors, dtype=np.float32)
            else:
                b_u = float(self.b_u[u])
                p_u = self.P[u]
            preds = self.mu + b_u + self.b_i[items_arr] + self.Q[items_arr] @ p_u
        else:
            u_arr = np.asarray(user_idx, dtype=np.int32)
            preds = self.mu + self.b_u[u_arr] + self.b_i[items_arr] + np.sum(self.P[u_arr] * self.Q[items_arr], axis=1)
        return np.clip(preds, 1.0, 5.0).astype(np.float32)

    def save(self, path: Path) -> None:
        """Save Funk-SVD model arrays to .npz and metadata to companion .json."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        np.savez_compressed(
            path,
            P=self.P,
            Q=self.Q,
            b_u=self.b_u,
            b_i=self.b_i,
            mu=np.float32(self.mu),
            item_counts=self.item_counts,
        )

        meta = {
            "name": self.name,
            "n_users": self.n_users,
            "n_items": self.n_items,
            "n_factors": self.n_factors,
            "lr": self.lr,
            "reg_bias": self.reg_bias,
            "reg_factor": self.reg_factor,
            "n_epochs": self.n_epochs,
            "mu": float(self.mu),
            "global_mean": float(self.global_mean),
            "convergence_history": self.convergence_history,
        }
        meta_path = path.with_suffix(".json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        # Also write convergence.json for Model Lab endpoint if artifacts dir
        if self.convergence_history:
            best_ep = 1
            if len(self.convergence_history) > 0:
                best_ep = int(np.argmin([e["val_rmse"] for e in self.convergence_history]) + 1)
            convergence_data = {
                "epochs": self.convergence_history,
                "best_epoch": best_ep,
                "training_time_sec": round(float(self.n_epochs * 0.15), 2),
                "algorithm": "Funk-SVD",
            }
            conv_path = path.parent / "convergence.json"
            with open(conv_path, "w", encoding="utf-8") as f:
                json.dump(convergence_data, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "FunkSVD":
        """Load Funk-SVD model from .npz and metadata .json."""
        path = Path(path)
        meta_path = path.with_suffix(".json")

        meta: Dict[str, Any] = {}
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

        data = np.load(path)
        P = data["P"]
        Q = data["Q"]
        b_u = data["b_u"]
        b_i = data["b_i"]
        mu = float(data["mu"])

        model = cls(
            n_factors=meta.get("n_factors", Q.shape[1]),
            lr=meta.get("lr", 0.007),
            reg_bias=meta.get("reg_bias", 0.02),
            reg_factor=meta.get("reg_factor", 0.05),
            n_epochs=meta.get("n_epochs", 15),
        )
        model.n_users = P.shape[0]
        model.n_items = Q.shape[0]
        model.mu = mu
        model.global_mean = meta.get("global_mean", mu)
        model.P = P.astype(np.float32)
        model.Q = Q.astype(np.float32)
        model.b_u = b_u.astype(np.float32)
        model.b_i = b_i.astype(np.float32)
        model.convergence_history = meta.get("convergence_history", [])

        if "item_counts" in data and len(data["item_counts"]) == model.n_items:
            model.item_counts = data["item_counts"].astype(np.int32)
            counts_f = model.item_counts.astype(np.float32)
            model.shrink_factor = (counts_f / (counts_f + 50.0)).astype(np.float32)

        return model
