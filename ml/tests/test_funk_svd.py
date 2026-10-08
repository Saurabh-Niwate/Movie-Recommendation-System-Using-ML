"""Unit tests for Funk-SVD with Numba SGD, online fold-in, and explainability."""
import tempfile
from pathlib import Path
import numpy as np
import pytest
import scipy.sparse as sp

from recsys.models.funk_svd import FunkSVD


@pytest.fixture
def svd_rating_matrix():
    """Create a 12-user, 8-item sparse matrix for SGD factorization testing."""
    rng = np.random.RandomState(42)
    # Latent true rank-2 matrix
    U_true = rng.normal(0, 1, (12, 2))
    V_true = rng.normal(0, 1, (8, 2))
    R_dense = 3.5 + U_true @ V_true.T
    # Mask out 60% of entries
    mask = rng.rand(12, 8) > 0.4
    R_dense[~mask] = 0.0
    R_dense = np.clip(R_dense, 1.0, 5.0)
    R_dense[~mask] = 0.0
    return sp.csr_matrix(R_dense, dtype=np.float32)


def test_funk_svd_sgd_convergence(svd_rating_matrix):
    """Test that Numba SGD training reduces training loss over epochs."""
    R = svd_rating_matrix
    model = FunkSVD(n_factors=4, lr=0.01, n_epochs=10, random_state=42)
    model.fit(R, verbose=False)

    assert len(model.convergence_history) == 10
    first_loss = model.convergence_history[0]["train_loss"]
    final_loss = model.convergence_history[-1]["train_loss"]

    # Final loss should be lower than initial loss
    assert final_loss < first_loss
    assert model.P.shape == (12, 4)
    assert model.Q.shape == (8, 4)
    assert len(model.b_u) == 12
    assert len(model.b_i) == 8


def test_funk_svd_online_fold_in_ridge_solution(svd_rating_matrix):
    """Test that online fold-in solves the analytical Ridge regression system."""
    R = svd_rating_matrix
    model = FunkSVD(n_factors=4, lr=0.01, n_epochs=5, random_state=42).fit(R, verbose=False)

    # Test user with 3 ratings
    user_ratings = {0: 5.0, 2: 4.0, 5: 3.5}
    b_u, p_u = model.fold_in(user_ratings)

    assert isinstance(b_u, float)
    assert isinstance(p_u, np.ndarray)
    assert len(p_u) == model.n_factors

    # Verify against manual Ridge regression solution
    items = np.array([0, 2, 5], dtype=np.int32)
    ratings = np.array([5.0, 4.0, 3.5], dtype=np.float32)
    y = ratings - model.mu - model.b_i[items]
    Q_tilde = np.hstack([np.ones((3, 1), dtype=np.float32), model.Q[items]])
    Lambda = np.zeros((5, 5), dtype=np.float32)
    Lambda[0, 0] = model.reg_bias
    np.fill_diagonal(Lambda[1:, 1:], model.reg_factor)

    expected_w = np.linalg.solve(Q_tilde.T @ Q_tilde + Lambda, Q_tilde.T @ y)

    assert pytest.approx(b_u, abs=1e-5) == expected_w[0]
    np.testing.assert_allclose(p_u, expected_w[1:], rtol=1e-5)


def test_funk_svd_cold_start_fold_in(svd_rating_matrix):
    """Test that cold-start users (empty ratings) fold-in to zero bias and factor."""
    R = svd_rating_matrix
    model = FunkSVD(n_factors=4, n_epochs=2).fit(R, verbose=False)

    # Empty dict
    b_u, p_u = model.fold_in({})
    assert b_u == 0.0
    np.testing.assert_allclose(p_u, 0.0)

    # Empty CSR
    empty_csr = sp.csr_matrix((1, 8), dtype=np.float32)
    b_u_csr, p_u_csr = model.fold_in(empty_csr)
    assert b_u_csr == 0.0
    np.testing.assert_allclose(p_u_csr, 0.0)

    # Cold start predictions must equal mu + b_i
    preds = model.predict(empty_csr, np.array([0, 1, 2]))
    expected_preds = np.clip(model.mu + model.b_i[np.array([0, 1, 2])], 1.0, 5.0)
    np.testing.assert_allclose(preds, expected_preds, atol=1e-5)


def test_funk_svd_explainability(svd_rating_matrix):
    """Test mathematical consistency of Funk-SVD explainability endpoint."""
    R = svd_rating_matrix
    model = FunkSVD(n_factors=4, n_epochs=5).fit(R, verbose=False)

    user_vec = R.getrow(0)
    target_item = 2
    expl = model.explain(user_vec, target_item)

    assert "mu" in expl
    assert "user_bias" in expl
    assert "item_bias" in expl
    assert "dot_product" in expl
    assert "latent_breakdown" in expl
    assert "predicted_score" in expl

    # Check that sum of latent products equals dot_product
    sum_products = sum(item["product"] for item in expl["latent_breakdown"])
    assert pytest.approx(expl["dot_product"], abs=1e-5) == sum_products

    # Check predicted_score = clip(mu + user_bias + item_bias + dot_product)
    expected_score = float(np.clip(
        expl["mu"] + expl["user_bias"] + expl["item_bias"] + expl["dot_product"],
        1.0,
        5.0,
    ))
    assert pytest.approx(expl["predicted_score"], abs=1e-5) == expected_score


def test_funk_svd_save_and_load(svd_rating_matrix, tmp_path):
    """Test saving to .npz/.json and restoring FunkSVD model."""
    R = svd_rating_matrix
    model = FunkSVD(n_factors=4, lr=0.01, n_epochs=5, random_state=42).fit(R, verbose=False)

    save_path = tmp_path / "funk_svd.npz"
    model.save(save_path)
    assert save_path.exists()
    assert save_path.with_suffix(".json").exists()

    loaded = FunkSVD.load(save_path)
    assert loaded.n_users == model.n_users
    assert loaded.n_items == model.n_items
    assert loaded.n_factors == model.n_factors
    assert pytest.approx(loaded.mu, abs=1e-5) == model.mu

    user_vec = R.getrow(3)
    items = np.array([1, 3, 5])
    np.testing.assert_allclose(model.predict(user_vec, items), loaded.predict(user_vec, items), atol=1e-5)
    np.testing.assert_allclose(model.score_all(user_vec), loaded.score_all(user_vec), atol=1e-5)
