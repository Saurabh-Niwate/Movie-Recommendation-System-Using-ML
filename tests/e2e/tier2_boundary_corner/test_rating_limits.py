"""Tier 2: Boundary & Corner Cases - Rating Value Limits & Schema Validation.

Verifies:
- Minimum valid boundary rating 1.0
- Maximum valid boundary rating 5.0
- Sub-minimum rejection (0.0, -1.0)
- Super-maximum rejection (5.5, 10.0)
- Re-rating behavior (mutation without duplication)
- Fractional rating precision support
"""


def test_rating_minimum_boundary_1_0(client):
    """T2.2.1: Verify lowest allowed star rating (1.0) is accepted."""
    response = client.post("/api/v1/profiles/neel/ratings", json={"movie_id": 1, "rating": 1.0})
    assert response.status_code == 200
    res = response.json()
    assert res["rating"] == 1.0


def test_rating_maximum_boundary_5_0(client):
    """T2.2.2: Verify highest allowed star rating (5.0) is accepted."""
    response = client.post("/api/v1/profiles/neel/ratings", json={"movie_id": 1, "rating": 5.0})
    assert response.status_code == 200
    res = response.json()
    assert res["rating"] == 5.0


def test_rating_below_minimum_rejected(client):
    """T2.2.3: Verify submitting rating < 1.0 (e.g. 0.0 or 0.5) is rejected with 422."""
    for invalid_val in [0.0, 0.9, -1.0]:
        response = client.post(
            "/api/v1/profiles/neel/ratings", json={"movie_id": 1, "rating": invalid_val}
        )
        assert response.status_code == 422, f"Value {invalid_val} should be rejected with 422"


def test_rating_above_maximum_rejected(client):
    """T2.2.4: Verify submitting rating > 5.0 (e.g. 5.1, 10.0) is rejected with 422."""
    for invalid_val in [5.1, 6.0, 10.0]:
        response = client.post(
            "/api/v1/profiles/neel/ratings", json={"movie_id": 1, "rating": invalid_val}
        )
        assert response.status_code == 422, f"Value {invalid_val} should be rejected with 422"


def test_rerating_updates_existing_movie(client):
    """T2.2.5: Verify re-rating a movie updates value without inflating ratings count."""
    # First rating
    res1 = client.post("/api/v1/profiles/mukesh/ratings", json={"movie_id": 1, "rating": 2.0})
    assert res1.status_code == 200
    count1 = res1.json()["ratings_count"]

    # Re-rate same movie
    res2 = client.post("/api/v1/profiles/mukesh/ratings", json={"movie_id": 1, "rating": 5.0})
    assert res2.status_code == 200
    count2 = res2.json()["ratings_count"]

    assert count1 == count2, (
        f"Count should not increase on re-rating: before={count1}, after={count2}"
    )
    assert res2.json()["rating"] == 5.0


def test_fractional_rating_precision_support(client):
    """T2.2.6: Verify half-star ratings like 3.5 and 4.5 are accepted."""
    for half_star in [2.5, 3.5, 4.5]:
        response = client.post(
            "/api/v1/profiles/neel/ratings", json={"movie_id": 1, "rating": half_star}
        )
        assert response.status_code == 200
        assert response.json()["rating"] == half_star
