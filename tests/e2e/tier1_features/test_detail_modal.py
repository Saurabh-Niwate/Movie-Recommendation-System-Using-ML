"""Tier 1: Feature Coverage - Title Detail Modal & Interactive Ratings.

Verifies:
- Detailed movie schema for modal presentation
- 404 error handling for invalid title IDs
- Interactive rating submission and fold-in response
- "More Like This" similar item recommendations
- Starter catalog grid for discovery
- Field type compliance
"""


def test_movie_detail_schema(client):
    """T1.4.1: Verify detailed movie endpoint returns complete metadata for modal."""
    response = client.get("/api/v1/movies/1")
    assert response.status_code == 200
    movie = response.json()
    assert movie["movie_id"] == 1
    assert movie.get("title")
    assert "year" in movie and isinstance(movie["year"], int)
    assert "genres" in movie and isinstance(movie["genres"], list)
    assert "synopsis" in movie
    assert "cast" in movie and isinstance(movie["cast"], list)
    assert "director" in movie
    assert "poster_path" in movie
    assert "backdrop_path" in movie


def test_movie_detail_nonexistent_returns_404(client):
    """T1.4.2: Verify querying nonexistent movie returns 404 Not Found."""
    response = client.get("/api/v1/movies/999999")
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error
    assert "999999" in str(error["detail"])


def test_submit_rating_valid(client):
    """T1.4.3: Verify submitting a valid rating succeeds and returns fold-in stats."""
    payload = {"movie_id": 1, "rating": 4.5}
    response = client.post("/api/v1/profiles/neel/ratings", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "ok"
    assert res["profile_id"] == "neel"
    assert res["movie_id"] == 1
    assert res["rating"] == 4.5
    assert "ratings_count" in res
    assert "fold_in_time_ms" in res
    assert res["fold_in_time_ms"] < 100.0, (
        f"Fold-in took {res['fold_in_time_ms']}ms, expected < 100ms"
    )


def test_more_like_this_items(client):
    """T1.4.4: Verify 'More like this' modal section returns related items with valid schema."""
    response = client.get("/api/v1/recommendations/also-watched/1")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    recs = data["recommendations"]
    assert len(recs) > 0
    for r in recs:
        assert "movie_id" in r
        assert "title" in r
        assert "match_percentage" in r
        assert 0 <= r["match_percentage"] <= 100


def test_starter_movies_grid(client):
    """T1.4.5: Verify starter movies endpoint returns 24 diverse popular movies."""
    response = client.get("/api/v1/movies/starter")
    assert response.status_code == 200
    movies = response.json()
    assert len(movies) == 24, f"Expected 24 starter movies, got {len(movies)}"
    # Verify diversity across genres
    all_genres = {g for m in movies for g in m["genres"]}
    assert len(all_genres) >= 4, f"Expected at least 4 distinct genres, got {all_genres}"


def test_movie_detail_field_types(client):
    """T1.4.6: Verify strict typing on movie detail payload fields."""
    response = client.get("/api/v1/movies/2571")
    assert response.status_code == 200
    m = response.json()
    assert isinstance(m["movie_id"], int)
    assert isinstance(m["title"], str)
    assert isinstance(m["year"], int)
    assert isinstance(m["genres"], list)
    assert isinstance(m["vote_average"], (int, float))
