"""Tier 1: Feature Coverage - Model Lab Dashboard.

Verifies:
- Live model leaderboard with comparative metrics
- Funk-SVD training convergence curves (epochs 1..20)
- Side-by-side Item-KNN vs Funk-SVD recommendation comparison
- Funk-SVD mathematical explainability breakdown (mu + b_u + b_i + p_u . q_i)
- Item-KNN mathematical explainability breakdown (user_mean + neighbor weights)
- Invalid model parameter validation
"""


def test_leaderboard_all_models(client):
    """T1.5.1: Verify leaderboard returns all 3 models and Funk-SVD/Item-KNN beat Popularity."""
    response = client.get("/api/v1/model-lab/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    models = {m["model_id"]: m for m in data["models"]}
    assert "popularity" in models
    assert "item_knn" in models
    assert "funk_svd" in models

    # Acceptance criteria verification:
    # Item-KNN and Funk-SVD must outperform Popularity baseline on NDCG@10 and RMSE
    pop = models["popularity"]
    knn = models["item_knn"]
    svd = models["funk_svd"]

    assert svd["ndcg_10"] > pop["ndcg_10"], "Funk-SVD NDCG@10 must beat Popularity"
    assert knn["ndcg_10"] > pop["ndcg_10"], "Item-KNN NDCG@10 must beat Popularity"
    assert svd["rmse"] < pop["rmse"], "Funk-SVD RMSE must be lower than Popularity"
    assert knn["rmse"] < pop["rmse"], "Item-KNN RMSE must be lower than Popularity"


def test_convergence_curve_epochs(client):
    """T1.5.2: Verify convergence curves contain 20 epochs with downward loss trajectory."""
    response = client.get("/api/v1/model-lab/convergence")
    assert response.status_code == 200
    epochs = response.json()
    assert isinstance(epochs, list)
    assert len(epochs) >= 15

    # Check downward loss trend
    first_loss = epochs[0]["train_loss"]
    last_loss = epochs[-1]["train_loss"]
    assert first_loss > last_loss, f"Loss did not decrease: initial={first_loss}, final={last_loss}"

    # Check downward validation RMSE trend
    first_rmse = epochs[0]["val_rmse"]
    last_rmse = epochs[-1]["val_rmse"]
    assert first_rmse > last_rmse, (
        f"Val RMSE did not decrease: initial={first_rmse}, final={last_rmse}"
    )


def test_model_compare_side_by_side(client):
    """T1.5.3: Verify side-by-side comparison endpoint returns both Funk-SVD and Item-KNN sets."""
    response = client.get("/api/v1/model-lab/compare?profile_id=neel")
    assert response.status_code == 200
    data = response.json()
    assert data["profile_id"] == "neel"
    assert "funk_svd" in data and len(data["funk_svd"]) > 0
    assert "item_knn" in data and len(data["item_knn"]) > 0


def test_explain_funk_svd_math(client):
    """T1.5.4: Verify Funk-SVD explainability endpoint decomposes score into mu + b_u + b_i + dot."""
    response = client.get("/api/v1/model-lab/explain?profile_id=neel&movie_id=2571&model=funk_svd")
    assert response.status_code == 200
    exp = response.json()
    assert exp["model"] == "funk_svd"
    assert exp["movie_id"] == 2571

    # Verify mathematical components
    mu = exp["global_mean"]
    bu = exp["user_bias"]
    bi = exp["item_bias"]
    dot = exp["latent_dot_product"]
    predicted = exp["predicted_score"]

    expected_sum = round(mu + bu + bi + dot, 2)
    assert abs(predicted - expected_sum) <= 0.05, (
        f"Mathematical identity failed: {predicted} != {expected_sum} ({mu} + {bu} + {bi} + {dot})"
    )


def test_explain_item_knn_math(client):
    """T1.5.5: Verify Item-KNN explainability endpoint returns neighbor similarity contributions."""
    response = client.get("/api/v1/model-lab/explain?profile_id=neel&movie_id=2571&model=item_knn")
    assert response.status_code == 200
    exp = response.json()
    assert exp["model"] == "item_knn"
    assert "user_mean" in exp
    assert "neighbors" in exp
    assert len(exp["neighbors"]) > 0
    for n in exp["neighbors"]:
        assert "similarity" in n and -1.0 <= n["similarity"] <= 1.0
        assert "rating" in n
        assert "contribution" in n


def test_explain_invalid_model_rejected(client):
    """T1.5.6: Verify explain endpoint rejects unsupported model names with 422 error."""
    response = client.get(
        "/api/v1/model-lab/explain?profile_id=neel&movie_id=2571&model=random_forest"
    )
    assert response.status_code == 422
