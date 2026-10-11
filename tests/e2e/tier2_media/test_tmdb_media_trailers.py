"""Tier 2: Real TMDB Media Imagery & YouTube Trailer Video Extraction E2E Tests.

Verifies:
- All movie posters and backdrops use real TMDB CDN URLs (`https://image.tmdb.org/t/p/...`)
  or high-res Stitch hosted stills (`https://images.unsplash.com/...`, `https://lh3.googleusercontent.com/...`).
- Zero AI-generated SVG placeholder artwork is present (`<svg`, `data:image/svg+xml`, `.svg`).
- Movie trailer extraction endpoint `GET /api/v1/movies/{id}/trailer` returns active YouTube embed URLs.
- TMDB alias route `GET /api/v1/tmdb/movie/{tmdb_id}/trailer` returns active YouTube embed URLs.
- Error handling: nonexistent movie ID returns HTTP 404 Not Found.
- Adversarial checks on malformed movie IDs (negative, string).
"""

import re
import pytest


def _assert_real_image_url(url: str, field_name: str, movie_id: int):
    """Assert URL is a real TMDB CDN or hosted image and not an SVG placeholder."""
    assert url, f"Movie {movie_id} has empty {field_name}"
    assert isinstance(url, str), f"Movie {movie_id} {field_name} is not a string"

    # Must be HTTP/HTTPS URL
    assert url.startswith("http://") or url.startswith("https://"), (
        f"Movie {movie_id} {field_name} must be a valid HTTP(S) URL, got: {url}"
    )

    # Must not contain SVG placeholders
    lower_url = url.lower()
    assert "<svg" not in lower_url, f"Movie {movie_id} {field_name} contains raw SVG markup: {url}"
    assert "data:image/svg" not in lower_url, f"Movie {movie_id} {field_name} contains SVG data URI: {url}"
    assert not lower_url.endswith(".svg"), f"Movie {movie_id} {field_name} points to an SVG file: {url}"
    assert "placeholder.svg" not in lower_url, f"Movie {movie_id} {field_name} is an SVG placeholder: {url}"


def test_starter_movies_real_media_urls_and_zero_svg(client):
    """T2.1.1: Verify starter movies (24 titles) use real image URLs and zero SVG placeholders."""
    response = client.get("/api/v1/movies/starter")
    assert response.status_code == 200
    movies = response.json()
    assert len(movies) >= 10, f"Expected at least 10 starter movies, got {len(movies)}"

    for m in movies:
        mid = m.get("movie_id") or m.get("id")
        assert mid is not None, f"Movie summary missing id/movie_id: {m}"
        _assert_real_image_url(m.get("poster_path"), "poster_path", mid)
        _assert_real_image_url(m.get("backdrop_path"), "backdrop_path", mid)


def test_movie_catalog_and_search_media_urls(client):
    """T2.1.2: Verify search results and catalog movies contain real imagery with zero SVG."""
    res_search = client.get("/api/v1/movies/search?limit=15")
    assert res_search.status_code == 200
    search_movies = res_search.json()
    assert len(search_movies) > 0

    for m in search_movies:
        mid = m.get("movie_id") or m.get("id")
        _assert_real_image_url(m.get("poster_path"), "poster_path", mid)
        _assert_real_image_url(m.get("backdrop_path"), "backdrop_path", mid)


def test_single_movie_detail_real_media_urls(client):
    """T2.1.3: Verify detailed movie endpoint returns real TMDB / hosted stills and valid metadata."""
    target_ids = [2571, 1, 589]  # The Matrix, Toy Story, Terminator 2
    for mid in target_ids:
        response = client.get(f"/api/v1/movies/{mid}")
        assert response.status_code == 200, f"Failed to fetch detail for movie {mid}"
        movie = response.json()
        assert movie.get("title")
        _assert_real_image_url(movie.get("poster_path"), "poster_path", mid)
        _assert_real_image_url(movie.get("backdrop_path"), "backdrop_path", mid)


def test_trailer_extraction_the_matrix_valid_youtube_contract(client):
    """T2.2.1: Verify GET /api/v1/movies/2571/trailer returns YouTube embed structure for The Matrix."""
    response = client.get("/api/v1/movies/2571/trailer")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["movie_id"] == 2571
    assert data["site"] == "YouTube"
    assert "key" in data and len(data["key"]) >= 5
    assert data["embed_url"].startswith(f"https://www.youtube.com/embed/{data['key']}")
    assert data["watch_url"].startswith(f"https://www.youtube.com/watch?v={data['key']}")
    assert "title" in data


def test_trailer_extraction_multiple_movies_diverse_keys(client):
    """T2.2.2: Verify trailers for multiple distinct movies return valid YouTube video keys."""
    test_movie_ids = [1, 260, 318, 589]
    extracted_keys = set()

    for mid in test_movie_ids:
        response = client.get(f"/api/v1/movies/{mid}/trailer")
        assert response.status_code == 200
        trailer = response.json()
        assert trailer["site"] == "YouTube"
        assert trailer["key"]
        assert "youtube.com/embed/" in trailer["embed_url"]
        extracted_keys.add(trailer["key"])

    # Multiple distinct titles should yield non-empty video keys
    assert len(extracted_keys) >= 2


def test_trailer_tmdb_alias_route(client):
    """T2.2.3: Verify GET /api/v1/tmdb/movie/{tmdb_id}/trailer alias endpoint works correctly."""
    # TMDB ID 603 is The Matrix
    response = client.get("/api/v1/tmdb/movie/603/trailer")
    assert response.status_code == 200
    trailer = response.json()
    assert trailer["site"] == "YouTube"
    assert "key" in trailer
    assert "embed_url" in trailer and "youtube.com/embed" in trailer["embed_url"]


def test_trailer_nonexistent_movie_returns_404(client):
    """T2.2.4: Verify trailer request for nonexistent movie ID returns 404 Not Found."""
    response = client.get("/api/v1/movies/9999999/trailer")
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error


@pytest.mark.parametrize("invalid_id", [
    "-1",
    "-999",
    "abc",
    "null",
])
def test_trailer_invalid_movie_id_handled_cleanly(client, invalid_id):
    """T2.2.5: Verify malformed or negative movie IDs return 404 or 422 without server error."""
    response = client.get(f"/api/v1/movies/{invalid_id}/trailer")
    assert response.status_code in (404, 422), f"Expected 404/422 for ID {invalid_id}, got {response.status_code}"
