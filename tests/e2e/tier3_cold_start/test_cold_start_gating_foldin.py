"""Tier 3: 6-Movie Cold-Start Gating & Online Fold-In E2E Tests.

Verifies:
- Cold-start gating: accounts with <6 ratings receive HTTP 403 Forbidden on /api/v1/recommendations.
- Incremental progression: 1, 2, 3, 4, and 5 ratings remain gated with 403.
- Cold-start unlock: submitting the 6th rating returns unlocked=True, updates is_cold_start=False,
  and unlocks HTTP 200 OK personalized recommendations.
- Sub-50ms analytical Ridge regression online fold-in execution.
- Star rating boundary validation (valid: 0.5 to 5.0; invalid: <0.5 or >5.0 return 422).
- Upsert semantics: re-rating an existing movie updates score without inflating ratings count.
- Authentication requirements: unauthenticated rating or recommendations requests return 401.
"""

import pytest


def _create_authenticated_user(client, email="coldstart.user@cinema.io"):
    """Helper to register a fresh user and return auth headers."""
    res = client.post("/api/v1/auth/signup", json={
        "email": email,
        "password": "Password123!",
        "name": "Cold Start Tester",
    })
    assert res.status_code == 201
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_cold_start_0_ratings_forbidden(client):
    """T3.1.1: Verify new user with 0 ratings receives 403 Forbidden on /api/v1/recommendations."""
    headers = _create_authenticated_user(client, "zero.ratings@cinema.io")

    response = client.get("/api/v1/recommendations", headers=headers)
    assert response.status_code == 403
    error = response.json()
    assert "detail" in error
    assert "at least 6 ratings" in error["detail"].lower() or "cold start" in error["detail"].lower()


def test_cold_start_incremental_progression_1_to_5_ratings_gated(client):
    """T3.1.2: Verify that having 1 through 5 ratings strictly keeps the user gated with 403."""
    headers = _create_authenticated_user(client, "incremental.user@cinema.io")
    starter_movies = [2571, 1, 589, 260, 318]  # 5 movies

    for idx, mid in enumerate(starter_movies, start=1):
        rate_res = client.post(
            "/api/v1/ratings",
            json={"movie_id": mid, "rating": 4.5},
            headers=headers,
        )
        assert rate_res.status_code == 200
        rate_data = rate_res.json()
        assert rate_data["ratings_count"] == idx
        assert rate_data["unlocked"] is False

        # Verify recommendations remain strictly gated
        rec_res = client.get("/api/v1/recommendations", headers=headers)
        assert rec_res.status_code == 403, f"Expected 403 after {idx} ratings, got {rec_res.status_code}"


def test_cold_start_unlock_on_6th_rating(client):
    """T3.1.3: Verify submitting the 6th rating flips is_cold_start to False and unlocks recommendations."""
    headers = _create_authenticated_user(client, "unlock.user@cinema.io")
    movies_to_rate = [2571, 1, 589, 260, 318, 527]  # Exactly 6 movies

    # Submit first 5 ratings
    for mid in movies_to_rate[:5]:
        client.post("/api/v1/ratings", json={"movie_id": mid, "rating": 4.0}, headers=headers)

    # Submit 6th rating
    sixth_res = client.post(
        "/api/v1/ratings",
        json={"movie_id": movies_to_rate[5], "rating": 5.0},
        headers=headers,
    )
    assert sixth_res.status_code == 200
    sixth_data = sixth_res.json()
    assert sixth_data["ratings_count"] == 6
    assert sixth_data["unlocked"] is True
    assert sixth_data["fold_in_time_ms"] < 50.0, f"Fold-in took {sixth_data['fold_in_time_ms']}ms, expected < 50ms"

    # Verify user profile state reflects unlock
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    user = me_res.json()
    assert user["ratings_count"] == 6
    assert user["is_cold_start"] is False

    # Verify recommendations are now unlocked (HTTP 200)
    rec_res = client.get("/api/v1/recommendations", headers=headers)
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert "items" in rec_data
    items = rec_data["items"]
    assert len(items) > 0

    # Rated movies must not appear in recommendations
    rated_set = set(movies_to_rate)
    rec_ids = [item["movie_id"] for item in items]
    overlap = rated_set.intersection(rec_ids)
    assert not overlap, f"Rated movies leaked into recommendation results: {overlap}"


def test_online_foldin_sub_50ms_latency(client):
    """T3.1.4: Verify online fold-in executes with latency well below the 50ms requirement."""
    headers = _create_authenticated_user(client, "latency.user@cinema.io")

    res = client.post(
        "/api/v1/ratings",
        json={"movie_id": 2571, "rating": 5.0},
        headers=headers,
    )
    assert res.status_code == 200
    fold_in_ms = res.json()["fold_in_time_ms"]
    assert fold_in_ms < 50.0, f"Expected fold-in latency < 50ms, got {fold_in_ms}ms"


@pytest.mark.parametrize("valid_rating", [0.5, 1.0, 2.5, 3.0, 4.5, 5.0])
def test_rating_boundary_valid_values(client, valid_rating):
    """T3.2.1: Verify star ratings within the [0.5, 5.0] range succeed."""
    headers = _create_authenticated_user(client, f"valid.rating.{valid_rating}@cinema.io")

    res = client.post(
        "/api/v1/ratings",
        json={"movie_id": 1, "rating": valid_rating},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.parametrize("invalid_rating", [0.0, -1.0, 5.5, 10.0, -99.0])
def test_rating_boundary_invalid_values_rejected(client, invalid_rating):
    """T3.2.2: Verify star ratings outside [0.5, 5.0] return HTTP 422 Unprocessable Entity."""
    headers = _create_authenticated_user(client, f"invalid.rating.{invalid_rating}@cinema.io")

    res = client.post(
        "/api/v1/ratings",
        json={"movie_id": 1, "rating": invalid_rating},
        headers=headers,
    )
    assert res.status_code == 422


def test_rating_upsert_does_not_increment_count(client):
    """T3.2.3: Verify updating an existing rating modifies score without inflating ratings_count."""
    headers = _create_authenticated_user(client, "upsert.user@cinema.io")

    # Rate movie 1 initially as 3.0
    res1 = client.post("/api/v1/ratings", json={"movie_id": 1, "rating": 3.0}, headers=headers)
    assert res1.json()["ratings_count"] == 1

    # Re-rate movie 1 as 5.0
    res2 = client.post("/api/v1/ratings", json={"movie_id": 1, "rating": 5.0}, headers=headers)
    assert res2.json()["ratings_count"] == 1, "Re-rating an already rated title must not increment count"


def test_rating_unauthenticated_returns_401(client):
    """T3.2.4: Verify submitting ratings without Bearer authorization returns 401."""
    res = client.post("/api/v1/ratings", json={"movie_id": 1, "rating": 4.5})
    assert res.status_code == 401


def test_rating_nonexistent_movie_returns_404(client):
    """T3.2.5: Verify submitting rating for nonexistent movie ID returns 404 Not Found."""
    headers = _create_authenticated_user(client, "nonexistent.movie@cinema.io")

    res = client.post(
        "/api/v1/ratings",
        json={"movie_id": 9999999, "rating": 4.5},
        headers=headers,
    )
    assert res.status_code == 404
