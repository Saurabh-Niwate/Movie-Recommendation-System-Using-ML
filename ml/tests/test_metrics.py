"""Unit tests for offline evaluation metrics."""
import numpy as np
import pytest

from recsys.eval.metrics import (
    compute_rmse,
    compute_mae,
    precision_at_k,
    recall_at_k,
    ndcg_at_k,
    catalog_coverage,
)


def test_rmse_and_mae():
    """Test RMSE and MAE calculations on known error arrays."""
    y_true = np.array([4.0, 3.0, 5.0, 2.0], dtype=np.float32)
    y_pred = np.array([3.0, 3.0, 4.0, 4.0], dtype=np.float32)
    # Errors: [1.0, 0.0, 1.0, -2.0]
    # Squared errors: [1, 0, 1, 4] -> mean = 6 / 4 = 1.5 -> sqrt(1.5) = 1.2247448...
    # Absolute errors: [1, 0, 1, 2] -> mean = 4 / 4 = 1.0
    assert pytest.approx(compute_rmse(y_true, y_pred), abs=1e-5) == np.sqrt(1.5)
    assert pytest.approx(compute_mae(y_true, y_pred), abs=1e-5) == 1.0

    # Perfect prediction
    assert compute_rmse(y_true, y_true) == 0.0
    assert compute_mae(y_true, y_true) == 0.0

    # Empty inputs
    assert compute_rmse(np.array([]), np.array([])) == 0.0
    assert compute_mae(np.array([]), np.array([])) == 0.0


def test_precision_and_recall_at_k():
    """Test Precision@K and Recall@K across perfect, zero, and partial matches."""
    relevant = {10, 20, 30}

    # Perfect top-3: ranked items are 10, 20, 30
    assert precision_at_k([10, 20, 30, 40, 50], relevant, k=3) == 1.0
    assert recall_at_k([10, 20, 30, 40, 50], relevant, k=3) == 1.0

    # Partial: 1 hit out of 5 recommendations
    assert precision_at_k([10, 99, 98, 97, 96], relevant, k=5) == 1.0 / 5.0
    assert recall_at_k([10, 99, 98, 97, 96], relevant, k=5) == 1.0 / 3.0

    # Zero hits
    assert precision_at_k([99, 98, 97], relevant, k=3) == 0.0
    assert recall_at_k([99, 98, 97], relevant, k=3) == 0.0

    # Empty relevant set
    assert recall_at_k([1, 2, 3], set(), k=3) == 0.0


def test_ndcg_at_k_discounting():
    """Test NDCG@K discounting property: earlier hits yield strictly higher scores."""
    relevant = {100}

    # Hit at position 1 (index 0): gain / log2(2) = 1 / 1 = 1.0 -> NDCG = 1.0
    ndcg_pos1 = ndcg_at_k([100, 20, 30, 40], relevant, k=4)
    assert pytest.approx(ndcg_pos1, abs=1e-5) == 1.0

    # Hit at position 2 (index 1): gain / log2(3) = 1 / 1.58496 -> NDCG < 1.0
    ndcg_pos2 = ndcg_at_k([10, 100, 30, 40], relevant, k=4)
    assert ndcg_pos2 < ndcg_pos1
    assert ndcg_pos2 > 0.0

    # Hit at position 4 (index 3) should be even lower
    ndcg_pos4 = ndcg_at_k([10, 20, 30, 100], relevant, k=4)
    assert ndcg_pos4 < ndcg_pos2

    # No hits
    assert ndcg_at_k([10, 20, 30], relevant, k=3) == 0.0
    # Empty relevant
    assert ndcg_at_k([10, 20], set(), k=2) == 0.0


def test_catalog_coverage():
    """Test catalog coverage computation."""
    recs = [1, 2, 3, 1, 2, 4]  # 4 unique items out of 10
    total_catalog = 10
    assert pytest.approx(catalog_coverage(recs, total_catalog), abs=1e-5) == 0.4

    # 100% coverage
    assert catalog_coverage(range(10), 10) == 1.0

    # Zero catalog
    assert catalog_coverage(recs, 0) == 0.0
