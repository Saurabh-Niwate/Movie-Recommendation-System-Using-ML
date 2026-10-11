"""Tier 1: Feature Coverage - Watchlist CRUD & Movie Catalog API.

Verifies:
- Querying pre-seeded watchlist items with enriched metadata
- Adding titles to a user's watchlist (HTTP 201)
- Removing titles from a user's watchlist (HTTP 200)
- Graceful handling of duplicate watchlist additions
- Error handling (404 Not Found) for invalid profiles and invalid movie IDs
- Dual mounting and root /watchlist endpoints
- Movie catalog listing GET /api/v1/movies with genre filtering and pagination
- Profile reset restoring watchlist to baseline state
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app as live_app


@pytest.fixture
def client():
    """Client fixture connected to CineMatch backend with state reset."""
    with TestClient(live_app) as test_client:
        test_client.post("/api/v1/profiles/reset")
        yield test_client
        test_client.post("/api/v1/profiles/reset")


def test_neel_preseeded_watchlist(client):
    """T1.6.1: Verify Neel profile contains pre-seeded watchlist items with enriched metadata."""
    response = client.get("/api/v1/profiles/neel/watchlist")
    assert response.status_code == 200
    watchlist = response.json()
    assert isinstance(watchlist, list)
    assert len(watchlist) >= 1

    for item in watchlist:
        assert "id" in item
        assert "movie_id" in item
        assert item["id"] == item["movie_id"]
        assert "title" in item
        assert "poster_path" in item
        assert "release_year" in item
        assert "genres" in item
        assert isinstance(item["genres"], list)
        assert "added_at" in item


def test_add_movie_to_watchlist(client):
    """T1.6.2: Verify adding a movie to a profile's watchlist returns HTTP 201 and updates list."""
    target_movie = 1  # Toy Story

    # Check initially empty for Mukesh
    init_res = client.get("/api/v1/profiles/mukesh/watchlist")
    assert init_res.status_code == 200
    assert target_movie not in [m["id"] for m in init_res.json()]

    # Add movie
    add_res = client.post(f"/api/v1/profiles/mukesh/watchlist/{target_movie}")
    assert add_res.status_code == 201
    payload = add_res.json()
    assert payload["status"] == "added"
    assert payload["profile_id"] == "mukesh"
    assert payload["movie_id"] == target_movie

    # Verify present in list
    check_res = client.get("/api/v1/profiles/mukesh/watchlist")
    assert check_res.status_code == 200
    saved_ids = [m["id"] for m in check_res.json()]
    assert target_movie in saved_ids


def test_remove_movie_from_watchlist(client):
    """T1.6.3: Verify removing a movie from a watchlist returns HTTP 200 and removes the title."""
    target_movie = 1

    # First add
    client.post(f"/api/v1/profiles/mukesh/watchlist/{target_movie}")

    # Then remove
    del_res = client.delete(f"/api/v1/profiles/mukesh/watchlist/{target_movie}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "removed"
    assert del_data["profile_id"] == "mukesh"
    assert del_data["movie_id"] == target_movie

    # Verify movie is gone
    check_res = client.get("/api/v1/profiles/mukesh/watchlist")
    assert check_res.status_code == 200
    assert target_movie not in [m["id"] for m in check_res.json()]


def test_duplicate_watchlist_addition_handles_cleanly(client):
    """T1.6.4: Verify duplicate additions succeed cleanly without unique constraint crashes."""
    target_movie = 260

    # Add first time
    r1 = client.post(f"/api/v1/profiles/mukesh/watchlist/{target_movie}")
    assert r1.status_code == 201

    # Add second time
    r2 = client.post(f"/api/v1/profiles/mukesh/watchlist/{target_movie}")
    assert r2.status_code == 201
    assert r2.json()["profile_id"] == "mukesh"


def test_watchlist_invalid_profile_returns_404(client):
    """T1.6.5: Verify 404 is raised when querying or modifying a non-existent profile."""
    bad_id = "nonexistent_persona_777"
    r_get = client.get(f"/api/v1/profiles/{bad_id}/watchlist")
    assert r_get.status_code == 404

    r_post = client.post(f"/api/v1/profiles/{bad_id}/watchlist/1")
    assert r_post.status_code == 404


def test_watchlist_invalid_movie_returns_404(client):
    """T1.6.6: Verify 404 is raised when adding or deleting an invalid movie ID."""
    r_post = client.post("/api/v1/profiles/mukesh/watchlist/99999999")
    assert r_post.status_code == 404

    r_del = client.delete("/api/v1/profiles/mukesh/watchlist/99999999")
    assert r_del.status_code == 404


def test_root_watchlist_endpoints(client):
    """T1.6.7: Verify /watchlist root path resolves profile via query and headers."""
    # Query parameter resolution
    r_query = client.get("/api/v1/watchlist?profile_id=neel")
    assert r_query.status_code == 200
    assert len(r_query.json()) >= 1

    # Header resolution
    r_header = client.get("/api/v1/watchlist", headers={"x-profile-id": "neel"})
    assert r_header.status_code == 200
    assert len(r_header.json()) >= 1

    # Path operation on root
    r_post = client.post("/api/v1/watchlist/1196?profile_id=mukesh")
    assert r_post.status_code == 201

    r_del = client.delete("/api/v1/watchlist/1196?profile_id=mukesh")
    assert r_del.status_code == 200


def test_catalog_endpoint_with_genre_filter(client):
    """T1.6.8: Verify GET /api/v1/movies catalog listing and genre filtering."""
    # Catalog listing
    res = client.get("/api/v1/movies")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 24

    # Genre filtering
    res_drama = client.get("/api/v1/movies?genre=Drama")
    assert res_drama.status_code == 200
    drama_data = res_drama.json()
    assert drama_data["genre"] == "Drama"
    assert drama_data["total"] > 0
    for m in drama_data["items"]:
        assert any("Drama" in g for g in m["genres"])


def test_profile_reset_restores_watchlist(client):
    """T1.6.9: Verify POST /api/v1/profiles/reset restores watchlists to clean seed state."""
    # Mukesh adds a movie
    client.post("/api/v1/profiles/mukesh/watchlist/1")
    assert len(client.get("/api/v1/profiles/mukesh/watchlist").json()) == 1

    # Trigger reset
    reset_res = client.post("/api/v1/profiles/reset")
    assert reset_res.status_code == 200

    # Mukesh watchlist should now be empty
    assert len(client.get("/api/v1/profiles/mukesh/watchlist").json()) == 0
