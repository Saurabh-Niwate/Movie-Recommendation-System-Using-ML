"""Unit tests for AssociationRules co-occurrence Lift model."""
from pathlib import Path
import numpy as np
import pytest
import scipy.sparse as sp

from recsys.models.association_rules import AssociationRules


@pytest.fixture
def binary_interaction_matrix():
    """Create a 5-user, 4-item interaction matrix.
    
    Users:
    0: {0, 1}
    1: {0, 1, 2}
    2: {0, 2}
    3: {1, 3}
    4: {0, 1, 2, 3}
    """
    # User 0: 0, 1
    # User 1: 0, 1, 2
    # User 2: 0, 2
    # User 3: 1, 3
    # User 4: 0, 1, 2, 3
    data = [1, 1,  1, 1, 1,  1, 1,  1, 1,  1, 1, 1, 1]
    rows = [0, 0,  1, 1, 1,  2, 2,  3, 3,  4, 4, 4, 4]
    cols = [0, 1,  0, 1, 2,  0, 2,  1, 3,  0, 1, 2, 3]
    return sp.csr_matrix((data, (rows, cols)), shape=(5, 4), dtype=np.float32)


def test_association_rules_support_and_lift_calculation(binary_interaction_matrix):
    """Verify item counts, co-occurrence counts, and Lift computation."""
    R = binary_interaction_matrix
    model = AssociationRules(min_cooccurrence=1, top_k=5).fit(R)

    # Item counts:
    # item 0 in {0, 1, 2, 4} -> 4
    # item 1 in {0, 1, 3, 4} -> 4
    # item 2 in {1, 2, 4} -> 3
    # item 3 in {3, 4} -> 2
    np.testing.assert_array_equal(model.item_counts, np.array([4, 4, 3, 2]))

    # For pair (2, 3):
    # Co-occurrence in user 4 only -> C_{2,3} = 1
    # Lift(2, 3) = (1 * 5) / (3 * 2) = 5/6 = 0.8333...
    # For pair (0, 2):
    # Co-occurrence in users 1, 2, 4 -> C_{0,2} = 3
    # Lift(0, 2) = (3 * 5) / (4 * 3) = 15/12 = 1.25
    recs_0 = model.get_also_watched(0)
    recs_0_dict = {item["item_idx"]: item for item in recs_0}
    assert 2 in recs_0_dict
    assert pytest.approx(recs_0_dict[2]["lift"], abs=1e-3) == 1.25
    assert recs_0_dict[2]["cooccurrence"] == 3


def test_association_rules_filtering(binary_interaction_matrix):
    """Test min_cooccurrence threshold filtering."""
    R = binary_interaction_matrix
    # Require at least 2 co-occurrences
    model = AssociationRules(min_cooccurrence=2).fit(R)

    # Pair (2, 3) had cooccurrence 1, so item 3 should NOT appear for item 2
    recs_2 = model.get_also_watched(2)
    items_for_2 = [item["item_idx"] for item in recs_2]
    assert 3 not in items_for_2


def test_association_rules_save_and_load(binary_interaction_matrix, tmp_path):
    """Test saving to JSON and Parquet and loading back."""
    R = binary_interaction_matrix
    model = AssociationRules(min_cooccurrence=1).fit(R)

    json_path = tmp_path / "associations.json"
    model.save(json_path)

    assert json_path.exists()
    assert (tmp_path / "associations.parquet").exists()

    loaded_json = AssociationRules.load(json_path)
    assert len(loaded_json.rules) == model.n_items

    # Compare also watched for item 0
    orig_0 = model.get_also_watched(0)
    loaded_0 = loaded_json.get_also_watched(0)
    assert orig_0 == loaded_0
