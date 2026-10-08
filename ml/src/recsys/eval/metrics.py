"""Evaluation metrics: RMSE, MAE, Precision@K, Recall@K, NDCG@K, Catalog Coverage."""
from typing import Set, Sequence, Iterable
import numpy as np


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Root Mean Squared Error."""
    if len(y_true) == 0:
        return 0.0
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Mean Absolute Error."""
    if len(y_true) == 0:
        return 0.0
    return float(np.mean(np.abs(y_true - y_pred)))


def precision_at_k(ranked_items: Sequence[int], relevant_items: Set[int], k: int = 10) -> float:
    """Precision@K: fraction of top-K recommended items that are relevant."""
    if k <= 0:
        return 0.0
    top_k = ranked_items[:k]
    hits = sum(1 for item in top_k if item in relevant_items)
    return hits / float(k)


def recall_at_k(ranked_items: Sequence[int], relevant_items: Set[int], k: int = 10) -> float:
    """Recall@K: fraction of relevant items that appear in top-K recommendations."""
    if not relevant_items:
        return 0.0
    top_k = ranked_items[:k]
    hits = sum(1 for item in top_k if item in relevant_items)
    return hits / float(len(relevant_items))


def ndcg_at_k(ranked_items: Sequence[int], relevant_items: Set[int], k: int = 10) -> float:
    """Normalized Discounted Cumulative Gain at K (binary relevance)."""
    if not relevant_items or k <= 0:
        return 0.0
    top_k = ranked_items[:k]
    gains = np.array([1.0 if item in relevant_items else 0.0 for item in top_k], dtype=np.float32)
    if gains.sum() == 0.0:
        return 0.0

    discounts = np.log2(np.arange(2, len(gains) + 2))
    dcg = float(np.sum(gains / discounts))

    # Ideal DCG: top items are all relevant (up to min(k, len(relevant_items)))
    n_ideal = min(k, len(relevant_items))
    ideal_discounts = np.log2(np.arange(2, n_ideal + 2))
    idcg = float(np.sum(1.0 / ideal_discounts))

    return dcg / idcg if idcg > 0.0 else 0.0


def catalog_coverage(all_recommended_items: Iterable[int], total_catalog_size: int) -> float:
    """Catalog Coverage: fraction of catalog items recommended at least once."""
    if total_catalog_size <= 0:
        return 0.0
    unique_recs = set(all_recommended_items)
    return len(unique_recs) / float(total_catalog_size)
