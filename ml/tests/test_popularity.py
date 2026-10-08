"""Unit tests for Popularity Bayesian weighted rating recommender."""
import json
import tempfile
from pathlib import Path
import numpy as np
import pytest
import scipy.sparse as sp

from recsys.models.popularity import PopularityRecommender


@pytest.fixture
def sample_rating_matrix():
    """Create a sample 5-user, 4-item rating matrix."""
    # User 0: items 0, 1
    # User 1: items 0, 1, 2
    # User 2: item 0
    # User 3: items 2, 3
    # User 4: items 0, 2
    data = [5.0, 4.0, 4.0, 3.0, 5.0, 5.0, 2.0, 1.0, 4.0, 3.0]
    rows = [0, 0, 1, 1, 1, 2, 3, 3, 4, 4]
    cols = [0, 1, 0, 1, 2, 0, 2, 3, 0, 2]
    return sp.csr_matrix((data, (rows, cols)), shape=(5, 4), dtype=np.float32)


def test_popularity_fit(sample_rating_matrix):
    """Test fitting PopularityRecommender and verifying item statistics."""
    R = sample_rating_matrix
    model = PopularityRecommender(damping=10.0).fit(R)

    assert model.n_users == 5
    assert model.n_items == 4
    # Global mean
    expected_mean = float(R.data.mean())
    assert pytest.approx(model.global_mean, abs=1e-5) == expected_mean

    # Item counts
    # item 0 rated by users 0, 1, 2, 4 -> count 4
    # item 1 rated by users 0, 1 -> count 2
    # item 2 rated by users 1, 3, 4 -> count 3
    # item 3 rated by user 3 -> count 1
    np.testing.assert_array_equal(model.item_counts, np.array([4, 2, 3, 1]))

    # Weighted ratings must be computed for all items
    assert len(model.weighted_ratings) == 4
    assert np.all(np.isfinite(model.weighted_ratings))


def test_popularity_predict(sample_rating_matrix):
    """Test predicting ratings with PopularityRecommender."""
    R = sample_rating_matrix
    model = PopularityRecommender().fit(R)

    user_vec = R.getrow(0)
    preds = model.predict(user_vec, np.array([0, 1, 2, 3]))

    assert len(preds) == 4
    # Predictions must be within [1.0, 5.0]
    assert np.all(preds >= 1.0)
    assert np.all(preds <= 5.0)

    # Item 0 (ratings: 5, 4, 5, 4; mean=4.5) should have higher predicted rating than item 3 (rating: 1)
    assert preds[0] > preds[3]


def test_popularity_recommend(sample_rating_matrix):
    """Test top-k recommendation generation."""
    R = sample_rating_matrix
    model = PopularityRecommender().fit(R)

    # User 0 has seen items 0 and 1
    user_0_vec = R.getrow(0)
    recs = model.recommend(user_0_vec, k=2, exclude_seen=True)

    # Must only recommend unseen items (2 and 3)
    recommended_items = [item for item, _ in recs]
    assert 0 not in recommended_items
    assert 1 not in recommended_items
    assert len(recs) <= 2


def test_popularity_save_and_load(sample_rating_matrix, tmp_path):
    """Test persistence to and loading from JSON."""
    R = sample_rating_matrix
    model = PopularityRecommender().fit(R)

    save_path = tmp_path / "popularity.json"
    model.save(save_path)
    assert save_path.exists()

    loaded = PopularityRecommender.load(save_path)
    assert loaded.n_users == model.n_users
    assert loaded.n_items == model.n_items
    assert pytest.approx(loaded.global_mean, abs=1e-5) == model.global_mean

    # Check identical predictions
    user_vec = R.getrow(2)
    items = np.array([0, 1, 2, 3])
    np.testing.assert_allclose(model.predict(user_vec, items), loaded.predict(user_vec, items))
