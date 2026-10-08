import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_leaderboard_endpoint():
    """Verify live leaderboard returns metrics for Popularity, Item-KNN, and Funk-SVD."""
    res = client.get("/api/v1/model-lab/leaderboard")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    models = data["models"]
    assert "popularity" in models
    assert "item_knn" in models
    assert "funk_svd" in models

    # Check metrics
    pop = models["popularity"]
    knn = models["item_knn"]
    svd = models["funk_svd"]

    assert svd["rmse"] < pop["rmse"]
    assert knn["rmse"] < pop["rmse"]
    assert svd["ndcg_10"] > pop["ndcg_10"]
    assert knn["ndcg_10"] > pop["ndcg_10"]


def test_convergence_endpoint():
    """Verify convergence curves return Funk-SVD epoch loss and validation RMSE history."""
    res = client.get("/api/v1/model-lab/convergence")
    assert res.status_code == 200
    data = res.json()
    assert data["algorithm"] == "Funk-SVD"
    assert "epochs" in data
    assert len(data["epochs"]) >= 10
    assert "best_epoch" in data
    for ep in data["epochs"]:
        assert "epoch" in ep
        assert "train_loss" in ep
        assert "val_rmse" in ep


def test_compare_models_side_by_side():
    """Verify side-by-side Top-10 recommendations for Item-KNN vs Funk-SVD."""
    res = client.get("/api/v1/model-lab/compare?profile_id=neel&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["profile_id"] == "neel"
    assert "item_knn" in data
    assert "funk_svd" in data
    assert len(data["item_knn"]) == 10
    assert len(data["funk_svd"]) == 10

    # Scores should be populated
    assert data["funk_svd"][0]["score"] > 0
    assert data["item_knn"][0]["score"] > 0


def test_explain_funk_svd_mathematical_breakdown():
    """Verify Funk-SVD mathematical explainability breakdown: mu + user_bias + item_bias + dot_product."""
    # Matrix movie id is 2571
    res = client.get("/api/v1/model-lab/explain?profile_id=neel&movie_id=2571&model=funk_svd")
    assert res.status_code == 200
    data = res.json()
    assert data["model"] == "funk_svd"
    assert data["profile_id"] == "neel"
    assert data["movie_id"] == 2571
    assert "The Matrix" in data["title"]

    mu = data["mu"]
    u_bias = data["user_bias"]
    i_bias = data["item_bias"]
    dot = data["dot_product"]
    pred = data["predicted_score"]

    # Mathematical identity check: mu + user_bias + item_bias + dot_product ~= predicted_score (before clipping)
    calc_sum = round(mu + u_bias + i_bias + dot, 4)
    # Since clipping is [1.0, 5.0], if calc_sum is within range, it must equal pred
    if 1.0 <= calc_sum <= 5.0:
        assert abs(calc_sum - pred) < 0.05, f"Expected {calc_sum} ~= {pred}"

    # Verify latent factors breakdown
    factors = data["latent_breakdown"]
    assert len(factors) == 32
    for f in factors:
        assert "factor_index" in f
        assert "user_val" in f
        assert "item_val" in f
        assert "product" in f
        expected_prod = round(f["user_val"] * f["item_val"], 4)
        assert abs(f["product"] - expected_prod) < 0.001


def test_explain_item_knn_mathematical_breakdown():
    """Verify Item-KNN mathematical explainability breakdown: user_mean + neighbor contributions."""
    res = client.get("/api/v1/model-lab/explain?profile_id=neel&movie_id=2571&model=item_knn")
    assert res.status_code == 200
    data = res.json()
    assert data["model"] == "item_knn"
    assert data["profile_id"] == "neel"
    assert data["movie_id"] == 2571
    assert "user_mean" in data
    assert "neighbors" in data
    assert "predicted_score" in data
    assert 1.0 <= data["predicted_score"] <= 5.0

    neighbors = data["neighbors"]
    assert len(neighbors) > 0
    for n in neighbors:
        assert "similarity" in n
        assert "user_rating" in n
        assert "contribution" in n
        assert "title" in n
        assert n["similarity"] >= 0
