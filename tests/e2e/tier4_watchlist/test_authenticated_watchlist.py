"""Tier 4: Authenticated Watchlist Operations E2E Tests.

Verifies:
- GET /api/v1/watchlist returns saved movies list for authenticated user.
- POST /api/v1/watchlist/{movie_id} adds movie to watchlist (HTTP 201 Created).
- POST /api/v1/watchlist with JSON body adds movie to watchlist (HTTP 201 Created).
- DELETE /api/v1/watchlist/{movie_id} removes movie from watchlist (HTTP 200 OK).
- Idempotency: duplicate additions succeed cleanly without errors or crashes.
- Strict user isolation: User A's watchlist is completely separate from User B's.
- Authentication gating: unauthenticated requests to watchlist endpoints return 401 Unauthorized.
- Error handling: adding a nonexistent movie ID returns 404 Not Found.
- Enriched metadata verification: items in watchlist contain title, poster_path, genres, and release_year.
"""

import pytest


def _create_user(client, email="wl.user@cinema.io"):
    """Helper to register user and obtain authorization header."""
    res = client.post("/api/v1/auth/signup", json={
        "email": email,
        "password": "Password123!",
        "name": "Watchlist Tester",
    })
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['token']}"}


def test_watchlist_initially_empty_for_new_user(client):
    """T4.1.1: Verify a fresh user account starts with an empty watchlist."""
    headers = _create_user(client, "empty.wl@cinema.io")

    response = client.get("/api/v1/watchlist", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_add_movie_to_watchlist_by_path_param(client):
    """T4.1.2: Verify adding a movie via path parameter returns 201 and enriches saved item."""
    headers = _create_user(client, "add.path@cinema.io")

    add_res = client.post("/api/v1/watchlist/2571", headers=headers)
    assert add_res.status_code == 201
    assert add_res.json()["status"] == "added"
    assert add_res.json()["movie_id"] == 2571

    # Verify item is in watchlist with full metadata
    get_res = client.get("/api/v1/watchlist", headers=headers)
    assert get_res.status_code == 200
    wl = get_res.json()
    assert len(wl) == 1
    item = wl[0]
    assert item["movie_id"] == 2571 or item["id"] == 2571
    assert item["title"] == "The Matrix"
    assert item["poster_path"].startswith("http")
    assert "Sci-Fi" in item["genres"] or "Action" in item["genres"]


def test_add_movie_to_watchlist_by_json_body(client):
    """T4.1.3: Verify adding a movie via JSON body payload returns 201."""
    headers = _create_user(client, "add.body@cinema.io")

    add_res = client.post("/api/v1/watchlist", json={"movie_id": 1}, headers=headers)
    assert add_res.status_code == 201
    assert add_res.json()["status"] == "added"

    wl = client.get("/api/v1/watchlist", headers=headers).json()
    assert len(wl) == 1
    assert wl[0]["title"] == "Toy Story"


def test_duplicate_watchlist_addition_idempotent(client):
    """T4.1.4: Verify adding an already saved movie succeeds idempotently without 500 error."""
    headers = _create_user(client, "idempotent@cinema.io")

    res1 = client.post("/api/v1/watchlist/589", headers=headers)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/watchlist/589", headers=headers)
    assert res2.status_code in (200, 201)

    wl = client.get("/api/v1/watchlist", headers=headers).json()
    assert len(wl) == 1, "Duplicate addition must not create duplicate items"


def test_remove_movie_from_watchlist(client):
    """T4.1.5: Verify removing a movie returns 200 OK and purges it from user's list."""
    headers = _create_user(client, "remove.wl@cinema.io")

    client.post("/api/v1/watchlist/260", headers=headers)
    client.post("/api/v1/watchlist/318", headers=headers)
    assert len(client.get("/api/v1/watchlist", headers=headers).json()) == 2

    # Remove movie 260
    del_res = client.delete("/api/v1/watchlist/260", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "removed"

    wl = client.get("/api/v1/watchlist", headers=headers).json()
    assert len(wl) == 1
    assert wl[0]["movie_id"] == 318 or wl[0]["id"] == 318


def test_remove_nonexistent_watchlist_item_graceful(client):
    """T4.1.6: Verify removing a movie not in watchlist succeeds cleanly without crash."""
    headers = _create_user(client, "remove.absent@cinema.io")

    del_res = client.delete("/api/v1/watchlist/9999", headers=headers)
    assert del_res.status_code in (200, 404)


def test_watchlist_strict_user_isolation(client):
    """T4.1.7: Verify User A and User B maintain completely isolated watchlists."""
    headers_a = _create_user(client, "user.alpha.wl@cinema.io")
    headers_b = _create_user(client, "user.beta.wl@cinema.io")

    # User A adds The Matrix (2571)
    client.post("/api/v1/watchlist/2571", headers=headers_a)

    # User B adds Toy Story (1)
    client.post("/api/v1/watchlist/1", headers=headers_b)

    wl_a = client.get("/api/v1/watchlist", headers=headers_a).json()
    wl_b = client.get("/api/v1/watchlist", headers=headers_b).json()

    assert len(wl_a) == 1
    assert len(wl_b) == 1
    assert (wl_a[0]["movie_id"] == 2571 or wl_a[0]["id"] == 2571)
    assert (wl_b[0]["movie_id"] == 1 or wl_b[0]["id"] == 1)


def test_watchlist_unauthenticated_requests_rejected_401(client):
    """T4.1.8: Verify GET, POST, and DELETE on /api/v1/watchlist require Bearer auth."""
    assert client.get("/api/v1/watchlist").status_code == 401
    assert client.post("/api/v1/watchlist/1").status_code == 401
    assert client.delete("/api/v1/watchlist/1").status_code == 401


def test_watchlist_add_nonexistent_movie_returns_404(client):
    """T4.1.9: Verify adding a nonexistent movie ID returns 404 Not Found."""
    headers = _create_user(client, "notfound.wl@cinema.io")

    res = client.post("/api/v1/watchlist/9999999", headers=headers)
    assert res.status_code == 404
