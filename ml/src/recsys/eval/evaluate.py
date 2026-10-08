"""Model evaluation harness."""
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import scipy.sparse as sp
from joblib import Parallel, delayed
from recsys.config import ARTIFACTS_DIR, RELEVANCE_THRESHOLD
from recsys.eval.metrics import (
    compute_rmse,
    compute_mae,
    precision_at_k,
    recall_at_k,
    ndcg_at_k,
    catalog_coverage,
)
from recsys.models.base import Recommender


def evaluate_user(
    user_idx: int,
    train_vec: sp.csr_matrix,
    test_items: np.ndarray,
    test_ratings: np.ndarray,
    model: Recommender,
    k: int = 10,
    rel_thresh: float = RELEVANCE_THRESHOLD,
) -> Dict[str, Any]:
    """Evaluate one user for rating prediction and ranking metrics."""
    # 1. Rating prediction
    preds = model.predict(train_vec, test_items, user_idx=user_idx)
    errors = test_ratings - preds

    # 2. Ranking metrics
    relevant_items = set(test_items[test_ratings >= rel_thresh])
    if len(relevant_items) > 0:
        recs = model.recommend(train_vec, k=k, exclude_seen=True, user_idx=user_idx)
        ranked_items = [item_idx for item_idx, _ in recs]

        p = precision_at_k(ranked_items, relevant_items, k=k)
        r = recall_at_k(ranked_items, relevant_items, k=k)
        ndcg = ndcg_at_k(ranked_items, relevant_items, k=k)
    else:
        p, r, ndcg, ranked_items = None, None, None, []

    return {
        "user_idx": user_idx,
        "n_test": len(test_items),
        "errors": errors.tolist(),
        "p_at_k": p,
        "r_at_k": r,
        "ndcg_at_k": ndcg,
        "top_recs": ranked_items,
    }


def evaluate_model(
    model: Recommender,
    train_R: sp.csr_matrix,
    test_df: pd.DataFrame,
    k: int = 10,
    rel_thresh: float = RELEVANCE_THRESHOLD,
    n_jobs: int = -1,
) -> Dict[str, Any]:
    """Run full evaluation suite for a recommender model."""
    start_time = time.time()
    print(f"[recsys] Evaluating {model.name}...")

    # Group test items and ratings per user
    test_user_groups = test_df.groupby("user_idx")
    unique_users = list(test_user_groups.groups.keys())

    # Pre-extract user data
    user_payloads = [
        (
            uid,
            train_R.getrow(uid),
            group["item_idx"].to_numpy(dtype=np.int32),
            group["rating"].to_numpy(dtype=np.float32),
        )
        for uid, group in test_user_groups
    ]

    results = Parallel(n_jobs=n_jobs, backend="threading")(
        delayed(evaluate_user)(uid, uvec, items, ratings, model, k, rel_thresh)
        for uid, uvec, items, ratings in user_payloads
    )

    all_errors: List[float] = []
    p_scores: List[float] = []
    r_scores: List[float] = []
    ndcg_scores: List[float] = []
    all_recommended: List[int] = []

    for res in results:
        all_errors.extend(res["errors"])
        if res["p_at_k"] is not None:
            p_scores.append(res["p_at_k"])
            r_scores.append(res["r_at_k"])
            ndcg_scores.append(res["ndcg_at_k"])
        all_recommended.extend(res["top_recs"])

    errors_arr = np.array(all_errors, dtype=np.float32)
    rmse = float(np.sqrt(np.mean(errors_arr ** 2)))
    mae = float(np.mean(np.abs(errors_arr)))
    mean_p = float(np.mean(p_scores)) if p_scores else 0.0
    mean_r = float(np.mean(r_scores)) if r_scores else 0.0
    mean_ndcg = float(np.mean(ndcg_scores)) if ndcg_scores else 0.0
    cov = catalog_coverage(all_recommended, model.n_items)
    elapsed = time.time() - start_time

    display_names = {
        "popularity": "Bayesian Popularity Baseline",
        "item_knn": "Item-KNN (Adjusted Cosine)",
        "funk_svd": "Funk-SVD Matrix Factorization",
    }
    descriptions = {
        "popularity": "Global Bayesian average rating weighted by vote count threshold",
        "item_knn": "Item-based collaborative filtering with adjusted cosine similarity and shrinkage",
        "funk_svd": "Latent factor model with user/item biases trained via fast SGD",
    }

    metrics = {
        "model": model.name,
        "model_name": model.name,
        "display_name": display_names.get(model.name, model.name),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "precision_at_k": round(mean_p, 4),
        "precision_10": round(mean_p, 4),
        "recall_at_k": round(mean_r, 4),
        "recall_10": round(mean_r, 4),
        "ndcg_at_k": round(mean_ndcg, 4),
        "ndcg_10": round(mean_ndcg, 4),
        "coverage_at_k": round(cov, 4),
        "coverage_10": round(cov, 4),
        "description": descriptions.get(model.name, ""),
        "evaluated_users": len(results),
        "eval_seconds": round(elapsed, 2),
    }

    print(
        f"[recsys] {model.name} Results (k={k}): "
        f"RMSE: {metrics['rmse']:.4f} | MAE: {metrics['mae']:.4f} | "
        f"NDCG@{k}: {metrics['ndcg_at_k']:.4f} | P@{k}: {metrics['precision_at_k']:.4f} | "
        f"Coverage: {metrics['coverage_at_k']:.1%} ({elapsed:.1f}s)"
    )
    return metrics
