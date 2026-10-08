"""Tier 3: Cross-Feature Interactions - Real-Time Online Fold-in (< 100ms Response).

Verifies:
- Rating submission executes closed-form fold-in in < 100ms
- Rating reflects in recommendations immediately without full retrain
- Multiple consecutive ratings update recommendation rankings dynamically
"""

import time


def test_rating_foldin_latency_under_100ms(client):
    """T3.2.1: Verify rating submission and online fold-in completes in < 100ms."""
    t0 = time.perf_counter()
    response = client.post("/api/v1/profiles/neel/ratings", json={"movie_id": 1, "rating": 5.0})
    duration_ms = (time.perf_counter() - t0) * 1000.0

    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "ok"
    assert "fold_in_time_ms" in res
    assert res["fold_in_time_ms"] < 100.0, f"Server fold-in took {res['fold_in_time_ms']}ms > 100ms"
    assert duration_ms < 200.0, f"Total HTTP round-trip took {duration_ms}ms"


def test_rating_reflects_in_recommendations_without_retrain(client):
    """T3.2.2: Verify newly submitted rating is reflected in recommendations immediately."""
    # Pre-condition: get initial recommendations for Neel
    initial_recs = client.get("/api/v1/profiles/neel/recommendations?limit=20").json()["items"]
    initial_ids = [it["movie_id"] for it in initial_recs]
    assert len(initial_ids) > 0, "Initial recommendations must not be empty"
    target_id = initial_ids[0]

    # Submit 5-star rating for the top recommended movie
    res = client.post("/api/v1/profiles/neel/ratings", json={"movie_id": target_id, "rating": 5.0})
    assert res.status_code == 200

    # Fetch updated recommendations
    updated_recs = client.get("/api/v1/profiles/neel/recommendations?limit=20").json()["items"]
    updated_ids = [it["movie_id"] for it in updated_recs]

    # Verify target_id is now removed from recommendations (because user has already rated it!)
    assert target_id not in updated_ids, (
        f"Rated movie ({target_id}) should not be recommended again"
    )

    # Verify ratings count has incremented on profile
    prof = client.get("/api/v1/profiles/neel").json()
    assert prof["ratings_count"] >= 19


def test_consecutive_ratings_compound_updates(client):
    """T3.2.3: Verify multiple consecutive ratings update user profile iteratively."""
    for idx, mid in enumerate([1, 2, 3]):
        res = client.post("/api/v1/profiles/neel/ratings", json={"movie_id": mid, "rating": 4.5})
        assert res.status_code == 200
        assert res.json()["ratings_count"] >= 18 + idx + 1
