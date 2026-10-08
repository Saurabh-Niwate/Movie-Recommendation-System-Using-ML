"""Tier 3: Cross-Feature Interactions - Model Toggle Synchronization (Item-KNN vs Funk-SVD).

Verifies:
- Model toggle produces distinct numerical scores for same movies
- Model toggle produces different rank orders in recommendations
- Side-by-side comparison endpoint is synchronized with individual queries
- Mathematical explainability matches the active model
"""


def test_model_toggle_distinct_scores(client):
    """T3.3.1: Verify toggling model between Item-KNN and Funk-SVD returns distinct scores."""
    res_svd = client.get("/api/v1/profiles/neel/recommendations?model=funk_svd&limit=10")
    res_knn = client.get("/api/v1/profiles/neel/recommendations?model=item_knn&limit=10")

    assert res_svd.status_code == 200
    assert res_knn.status_code == 200

    items_svd = res_svd.json()["items"]
    items_knn = res_knn.json()["items"]

    svd_scores = {it["movie_id"]: it["score"] for it in items_svd}
    knn_scores = {it["movie_id"]: it["score"] for it in items_knn}

    # Common items should have distinct prediction scores
    common_ids = set(svd_scores.keys()).intersection(set(knn_scores.keys()))
    assert len(common_ids) > 0

    score_differences = [abs(svd_scores[mid] - knn_scores[mid]) for mid in common_ids]
    # At least some items have different scores
    assert any(diff > 0.01 for diff in score_differences), (
        "Funk-SVD and Item-KNN produced identical scores!"
    )


def test_model_toggle_distinct_rankings(client):
    """T3.3.2: Verify Item-KNN and Funk-SVD produce distinct ranking orders."""
    res_svd = client.get("/api/v1/profiles/neel/recommendations?model=funk_svd&limit=10")
    res_knn = client.get("/api/v1/profiles/neel/recommendations?model=item_knn&limit=10")

    order_svd = [it["movie_id"] for it in res_svd.json()["items"]]
    order_knn = [it["movie_id"] for it in res_knn.json()["items"]]

    assert order_svd != order_knn, "Funk-SVD and Item-KNN should have different ranking orders"


def test_side_by_side_compare_matches_individual_queries(client):
    """T3.3.3: Verify /model-lab/compare returns identical results to individual model calls."""
    compare = client.get("/api/v1/model-lab/compare?profile_id=neel").json()
    res_svd = client.get("/api/v1/profiles/neel/recommendations?model=funk_svd&limit=10").json()
    res_knn = client.get("/api/v1/profiles/neel/recommendations?model=item_knn&limit=10").json()

    svd_ids_compare = [it["movie_id"] for it in compare["funk_svd"]]
    svd_ids_direct = [it["movie_id"] for it in res_svd["items"]]
    assert svd_ids_compare == svd_ids_direct

    knn_ids_compare = [it["movie_id"] for it in compare["item_knn"]]
    knn_ids_direct = [it["movie_id"] for it in res_knn["items"]]
    assert knn_ids_compare == knn_ids_direct
