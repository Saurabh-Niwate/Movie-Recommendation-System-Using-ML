"""Verification of Furtado & Singh (2020) Table 5 replication.

Reference:
Furtado & Singh (2020), 'Movie recommendation system using machine learning',
International Journal of Research in Industrial Engineering, 9(1), 84-98.
Table 5 (page 91-92):
User A: EDM=1, Reggae=5, Trance=4
User B: EDM=2, Pop=3, Reggae=4
User C: EDM=4, Pop=5, Trance=2
User D: EDM=2, Reggae=4, Trance=5

The paper concludes (page 92):
'A has rated 4 for Trance, so next time when user B requests for a recommendation,
the system will recommend Trance to B since user A has rated 4 to Trance.'
"""
import numpy as np
import pytest
import scipy.sparse as sp

from recsys.models.item_knn import ItemKNN


@pytest.fixture
def table5_data():
    """Build the exact 4-user, 4-item rating matrix from Table 5."""
    # Rows: 0: A, 1: B, 2: C, 3: D
    # Cols: 0: EDM, 1: Pop, 2: Reggae, 3: Trance
    data = [
        # User A
        1.0, 5.0, 4.0,
        # User B
        2.0, 3.0, 4.0,
        # User C
        4.0, 5.0, 2.0,
        # User D
        2.0, 4.0, 5.0,
    ]
    rows = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3]
    cols = [0, 2, 3, 0, 1, 2, 0, 1, 3, 0, 2, 3]

    R = sp.csr_matrix((data, (rows, cols)), shape=(4, 4), dtype=np.float32)
    return R


def test_table5_user_means(table5_data):
    """Verify user mean ratings for Table 5."""
    R = table5_data
    # User A: (1 + 5 + 4) / 3 = 3.3333...
    assert pytest.approx(R.getrow(0).data.mean(), abs=1e-4) == 10.0 / 3.0
    # User B: (2 + 3 + 4) / 3 = 3.0
    assert pytest.approx(R.getrow(1).data.mean(), abs=1e-4) == 3.0
    # User C: (4 + 5 + 2) / 3 = 3.6667...
    assert pytest.approx(R.getrow(2).data.mean(), abs=1e-4) == 11.0 / 3.0
    # User D: (2 + 4 + 5) / 3 = 3.6667...
    assert pytest.approx(R.getrow(3).data.mean(), abs=1e-4) == 11.0 / 3.0


def test_table5_adjusted_cosine_similarity(table5_data):
    """Verify Adjusted Cosine similarity between items in Table 5."""
    R = table5_data
    knn = ItemKNN(k=4, shrink=0.0).fit(R)

    # Diagonal must be 0
    np.testing.assert_allclose(np.diag(knn.S), 0.0)

    # Reggae (2) and Trance (3) have positive similarity
    sim_reggae_trance = knn.S[2, 3]
    assert sim_reggae_trance > 0.0
    assert pytest.approx(sim_reggae_trance, abs=1e-3) == 0.3528
    # Symmetric
    assert pytest.approx(knn.S[3, 2], abs=1e-6) == knn.S[2, 3]


def test_table5_user_b_trance_prediction_equals_four(table5_data):
    """Verify the paper's key claim: User B's predicted rating for Trance is exactly 4.0."""
    R = table5_data
    knn = ItemKNN(k=4, shrink=0.0).fit(R)

    user_b_vec = R.getrow(1)
    preds = knn.predict(user_b_vec, np.array([3]))

    assert len(preds) == 1
    # Paper replication requirement: predicted rating for Trance is 4.0
    assert pytest.approx(preds[0], abs=1e-4) == 4.0


def test_table5_user_b_recommendation(table5_data):
    """Verify User B's top recommendation is Trance with score 4.0."""
    R = table5_data
    knn = ItemKNN(k=4, shrink=0.0).fit(R)

    user_b_vec = R.getrow(1)
    recs = knn.recommend(user_b_vec, k=1, exclude_seen=True)

    assert len(recs) == 1
    item_idx, score = recs[0]
    assert item_idx == 3  # Trance
    assert pytest.approx(score, abs=1e-4) == 4.0
