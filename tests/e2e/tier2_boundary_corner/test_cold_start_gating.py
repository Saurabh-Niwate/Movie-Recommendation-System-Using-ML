"""Tier 2: Boundary & Corner Cases - Mukesh Cold-Start Gating (Furtado & Singh 2020).

Verifies:
- 0 ratings -> 403 Forbidden
- 1..5 ratings -> 403 Forbidden with exact count tracking
- 6 ratings -> 200 OK unlocked boundary
- 7 ratings -> 200 OK stability beyond boundary
- Gating error message clarity
"""


def test_mukesh_0_ratings_forbidden(client):
    """T2.1.1: Verify Mukesh with 0 ratings is blocked with HTTP 403 Forbidden."""
    response = client.get("/api/v1/profiles/mukesh/recommendations")
    assert response.status_code == 403
    error = response.json()
    assert "detail" in error
    assert "at least 6 ratings" in error["detail"].lower()


def test_mukesh_1_rating_forbidden(client):
    """T2.1.2: Verify rating 1 movie still results in 403 Forbidden."""
    client.post("/api/v1/profiles/mukesh/ratings", json={"movie_id": 1, "rating": 5.0})
    response = client.get("/api/v1/profiles/mukesh/recommendations")
    assert response.status_code == 403
    error = response.json()
    assert "1/6" in error["detail"] or "5" in error["detail"]


def test_mukesh_5_ratings_forbidden(client):
    """T2.1.3: Verify boundary count of 5 ratings still results in 403 Forbidden."""
    # Rate 5 movies (IDs 1, 2571, 589, 260, 318)
    for mid in [1, 2571, 589, 260, 318]:
        res = client.post("/api/v1/profiles/mukesh/ratings", json={"movie_id": mid, "rating": 4.5})
        assert res.status_code == 200

    response = client.get("/api/v1/profiles/mukesh/recommendations")
    assert response.status_code == 403, f"Expected 403 at 5 ratings, got {response.status_code}"
    error = response.json()
    assert "5/6" in error["detail"] or "1" in error["detail"]


def test_mukesh_6_ratings_unlocked(client):
    """T2.1.4: Verify boundary count of 6 ratings unlocks personalized recommendations (200 OK)."""
    # Rate 6 movies
    mids = [1, 2571, 589, 260, 318, 527]
    for mid in mids:
        res = client.post("/api/v1/profiles/mukesh/ratings", json={"movie_id": mid, "rating": 4.5})
        assert res.status_code == 200
        if mid == mids[-1]:
            assert res.json()["unlocked"] is True

    # Check recommendations unlocked
    response = client.get("/api/v1/profiles/mukesh/recommendations")
    assert response.status_code == 200, f"Expected 200 at 6 ratings, got {response.status_code}"
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0

    # Verify profile status updated
    prof_res = client.get("/api/v1/profiles/mukesh")
    assert prof_res.status_code == 200
    assert prof_res.json()["is_cold_start"] is False
    assert prof_res.json()["ratings_count"] == 6


def test_mukesh_7_ratings_stable(client):
    """T2.1.5: Verify adding a 7th rating maintains unlocked state and updates scores."""
    # Rate 7 movies
    for mid in [1, 2571, 589, 260, 318, 527, 1196]:
        client.post("/api/v1/profiles/mukesh/ratings", json={"movie_id": mid, "rating": 5.0})

    response = client.get("/api/v1/profiles/mukesh/recommendations")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) > 0

    prof_res = client.get("/api/v1/profiles/mukesh")
    assert prof_res.json()["ratings_count"] == 7
    assert prof_res.json()["is_cold_start"] is False


def test_gating_error_message_clarity(client):
    """T2.1.6: Verify error response clearly explains the 6-rating requirement."""
    response = client.get("/api/v1/profiles/mukesh/recommendations")
    assert response.status_code == 403
    detail = response.json()["detail"]
    assert "cold start" in detail.lower()
    assert "6" in detail
