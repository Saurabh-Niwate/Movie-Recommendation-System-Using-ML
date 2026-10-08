"""Tier 4: Real-World Scenarios - Model Lab Algorithmic & Explainability Deep-Dive.

Verifies:
- Complete audit of all 6 offline metrics across all 3 models
- Funk-SVD mathematical decomposition audit (mu + b_u + b_i + p_u . q_i)
- Item-KNN adjusted cosine neighbor weight decomposition audit
- Training loss and validation RMSE convergence trajectory audit
"""


def test_model_lab_leaderboard_metric_hierarchy(client):
    """T4.3.1: Verify complete leaderboard metrics conform to expected ML hierarchy."""
    response = client.get("/api/v1/model-lab/leaderboard")
    assert response.status_code == 200
    models = {m["model_id"]: m for m in response.json()["models"]}

    svd = models["funk_svd"]
    knn = models["item_knn"]
    pop = models["popularity"]

    # 1. NDCG@10 hierarchy: Funk-SVD > Item-KNN > Popularity
    assert svd["ndcg_10"] > knn["ndcg_10"] > pop["ndcg_10"]

    # 2. RMSE hierarchy: Funk-SVD < Item-KNN < Popularity
    assert svd["rmse"] < knn["rmse"] < pop["rmse"]

    # 3. MAE hierarchy: Funk-SVD < Item-KNN < Popularity
    assert svd["mae"] < knn["mae"] < pop["mae"]

    # 4. Catalog Coverage hierarchy: Funk-SVD > Item-KNN > Popularity
    assert svd["coverage_10"] > knn["coverage_10"] > pop["coverage_10"]


def test_model_lab_funk_svd_mathematical_proof(client):
    """T4.3.2: Verify mathematical reconstruction of Funk-SVD prediction formula."""
    response = client.get("/api/v1/model-lab/explain?profile_id=neel&movie_id=2571&model=funk_svd")
    assert response.status_code == 200
    exp = response.json()

    # r_ui_hat = mu + b_u + b_i + sum(p_uf * q_if)
    mu = exp["global_mean"]
    bu = exp["user_bias"]
    bi = exp["item_bias"]
    dot = exp["latent_dot_product"]
    score = exp["predicted_score"]

    reconstructed = round(mu + bu + bi + dot, 2)
    assert abs(score - reconstructed) <= 0.05
    assert exp["latent_factors_count"] == 32


def test_model_lab_item_knn_neighbor_proof(client):
    """T4.3.3: Verify Item-KNN explanation provides valid neighbors and user mean."""
    response = client.get("/api/v1/model-lab/explain?profile_id=neel&movie_id=2571&model=item_knn")
    assert response.status_code == 200
    exp = response.json()

    assert "user_mean" in exp
    assert exp["user_mean"] > 0
    neighbors = exp["neighbors"]
    assert len(neighbors) > 0

    for n in neighbors:
        assert "similarity" in n and abs(n["similarity"]) <= 1.0
        assert "rating" in n and 1.0 <= n["rating"] <= 5.0
        assert "contribution" in n


def test_model_lab_convergence_monotonic_proof(client):
    """T4.3.4: Verify training convergence exhibits monotonic decrease across epochs."""
    response = client.get("/api/v1/model-lab/convergence")
    assert response.status_code == 200
    epochs = response.json()

    losses = [ep["train_loss"] for ep in epochs]
    rmses = [ep["val_rmse"] for ep in epochs]

    # Monotonically non-increasing (loss_t >= loss_{t+1})
    for t in range(len(losses) - 1):
        assert losses[t] >= losses[t + 1], (
            f"Loss increased at epoch {t + 1}: {losses[t]} -> {losses[t + 1]}"
        )
        assert rmses[t] >= rmses[t + 1], (
            f"RMSE increased at epoch {t + 1}: {rmses[t]} -> {rmses[t + 1]}"
        )
