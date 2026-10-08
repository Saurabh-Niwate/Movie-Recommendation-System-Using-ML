"""Tier 2: Boundary & Corner Cases - Missing Assets & Graceful Fallbacks.

Verifies:
- Poster and backdrop path existence or graceful string URI fallback
- Safe handling of ratings on invalid movies (404)
- Safe handling of ratings on invalid profiles (404)
- Also-watched request on non-existent title handling (404)
- Unrated movie cold similarity handling
"""


def test_poster_path_format_resilience(client):
    """T2.4.1: Verify every movie payload includes a valid string poster_path."""
    response = client.get("/api/v1/movies/starter")
    assert response.status_code == 200
    for m in response.json():
        assert "poster_path" in m
        assert isinstance(m["poster_path"], str)
        assert len(m["poster_path"]) > 0


def test_backdrop_path_format_resilience(client):
    """T2.4.2: Verify hero billboard includes valid string backdrop_path."""
    response = client.get("/api/v1/recommendations/billboard?profile_id=neel")
    assert response.status_code == 200
    hero = response.json()
    assert "backdrop_path" in hero
    assert isinstance(hero["backdrop_path"], str)
    assert len(hero["backdrop_path"]) > 0


def test_rating_nonexistent_movie_returns_404(client):
    """T2.4.3: Verify attempting to rate a nonexistent movie returns 404 Not Found."""
    response = client.post(
        "/api/v1/profiles/neel/ratings", json={"movie_id": 9999999, "rating": 4.0}
    )
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error


def test_rating_nonexistent_profile_returns_404(client):
    """T2.4.4: Verify attempting to rate under a nonexistent profile returns 404 Not Found."""
    response = client.post(
        "/api/v1/profiles/phantom_user/ratings", json={"movie_id": 1, "rating": 4.0}
    )
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error


def test_also_watched_nonexistent_movie_returns_404(client):
    """T2.4.5: Verify requesting 'also watched' for an invalid movie returns 404 Not Found."""
    response = client.get("/api/v1/recommendations/also-watched/9999999")
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error


def test_because_you_liked_nonexistent_profile_returns_404(client):
    """T2.4.6: Verify 'because you liked' for invalid profile returns 404 Not Found."""
    response = client.get("/api/v1/recommendations/because-you-liked?profile_id=phantom_user")
    assert response.status_code == 404
