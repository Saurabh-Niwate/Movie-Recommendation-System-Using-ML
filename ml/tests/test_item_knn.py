"""Unit tests for ItemKNN recommender with Adjusted Cosine and Shrinkage."""
import tempfile
from pathlib import Path
import numpy as np
import pytest
import scipy.sparse as sp

from recsys.models.item_knn import ItemKNN


@pytest.fixture
def synthetic_matrix():
    """Create a synthetic rating matrix for KNN testing."""
    # 6 users, 5 items
    data = [
        # User 0
        4.0, 5.0, 3.0,
        # User 1
        5.0, 4.0, 4.0,
        # User 2
        2.0, 1.0, 2.0,
        # User 3
        3.0, 3.0, 4.0,
        # User 4
        5.0, 5.0,
        # User 5
        1.0, 2.0, 1.0,
    ]
    rows = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 5]
    cols = [0, 1, 2, 0, 1, 3, 1, 2, 4, 0, 2, 4, 0, 1, 2, 3, 4]
    return sp.csr_matrix((data, (rows, cols)), shape=(6, 5), dtype=np.float32)


def test_item_knn_properties(synthetic_matrix):
    """Test symmetry, diagonal zeros, and non-negativity of similarity matrix."""
    R = synthetic_matrix
    knn = ItemKNN(k=3, shrink=0.0).fit(R)

    assert knn.S.shape == (5, 5)
    # Diagonal must be 0
    np.testing.assert_allclose(np.diag(knn.S), 0.0)
    # Symmetric
    np.testing.assert_allclose(knn.S, knn.S.T, atol=1e-5)
    # Non-negative (negative similarities clipped)
    assert np.all(knn.S >= 0.0)


def test_significance_shrinkage(synthetic_matrix):
    """Test that significance shrinkage properly attenuates similarities."""
    R = synthetic_matrix
    knn_raw = ItemKNN(k=3, shrink=0.0).fit(R)
    knn_shrunk = ItemKNN(k=3, shrink=10.0).fit(R)

    # For positive similarities with finite co-counts, shrunk < raw
    pos_mask = (knn_raw.S > 0.0)
    assert np.all(knn_shrunk.S[pos_mask] <= knn_raw.S[pos_mask])

    # Specifically check attenuation factor n / (n + beta)
    for i in range(5):
        for j in range(5):
            if i != j and knn_raw.S[i, j] > 0:
                n_co = knn_raw.co_counts[i, j]
                expected_factor = n_co / (n_co + 10.0)
                assert pytest.approx(knn_shrunk.S[i, j], abs=1e-4) == knn_raw.S[i, j] * expected_factor


def test_item_knn_cold_user_fallback(synthetic_matrix):
    """Test fallback when user has rated 0 movies."""
    R = synthetic_matrix
    knn = ItemKNN(k=3, shrink=5.0).fit(R)

    # Empty user vector
    empty_vec = sp.csr_matrix((1, 5), dtype=np.float32)
    preds = knn.predict(empty_vec, np.array([0, 1, 2, 3, 4]))

    assert len(preds) == 5
    # Must fallback to global mean + item biases, within [1.0, 5.0]
    assert np.all(preds >= 1.0)
    assert np.all(preds <= 5.0)


def test_item_knn_explain(synthetic_matrix):
    """Test explanation of prediction based on neighbor contributions."""
    R = synthetic_matrix
    knn = ItemKNN(k=3, shrink=0.0).fit(R)

    user_vec = R.getrow(0)
    explanations = knn.explain(user_vec, item_idx=3, top_n=2)

    assert isinstance(explanations, list)
    for exp in explanations:
        assert "neighbor_item_idx" in exp
        assert "similarity" in exp
        assert "contribution" in exp
        assert exp["similarity"] >= 0.0


def test_item_knn_save_and_load(synthetic_matrix, tmp_path):
    """Test persistence to .npz and .json and reload consistency."""
    R = synthetic_matrix
    knn = ItemKNN(k=3, shrink=5.0).fit(R)

    save_path = tmp_path / "item_knn.npz"
    knn.save(save_path)
    assert save_path.exists()
    assert save_path.with_suffix(".json").exists()

    loaded = ItemKNN.load(save_path)
    assert loaded.n_users == knn.n_users
    assert loaded.n_items == knn.n_items
    assert loaded.k == knn.k
    assert loaded.shrink == knn.shrink

    user_vec = R.getrow(1)
    items = np.array([0, 2, 4])
    np.testing.assert_allclose(knn.predict(user_vec, items), loaded.predict(user_vec, items), atol=1e-5)
