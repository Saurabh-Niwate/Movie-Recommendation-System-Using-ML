"""Tier 2: Boundary & Corner Cases - Catalog Search & Adversarial Inputs.

Verifies:
- Empty query handling (no 500 error)
- Whitespace-only query handling
- Metacharacter and special regex injection resilience
- Non-existent token search returns empty array gracefully
- Single-character short query handling
- Case-insensitivity across mixed capitalizations
"""


def test_search_empty_query(client):
    """T2.3.1: Verify search with empty query string q='' returns catalog safely without 500."""
    response = client.get("/api/v1/movies/search?q=")
    assert response.status_code == 200
    movies = response.json()
    assert isinstance(movies, list)
    assert len(movies) > 0


def test_search_whitespace_only(client):
    """T2.3.2: Verify search with whitespace-only query string returns catalog safely."""
    response = client.get("/api/v1/movies/search?q=%20%20%20")
    assert response.status_code == 200
    movies = response.json()
    assert isinstance(movies, list)
    assert len(movies) > 0


def test_search_special_regex_characters(client):
    """T2.3.3: Verify special regex characters (.*+?[]()^$\\) do not crash the search engine."""
    malicious_queries = [
        ".*",
        "+",
        "???",
        "[a-z]+",
        "(.*)",
        "^The",
        "Matrix\\",
        "|",
        "{2,5}",
    ]
    for q in malicious_queries:
        response = client.get(f"/api/v1/movies/search?q={q}")
        assert response.status_code == 200, (
            f"Query '{q}' caused failure with status {response.status_code}"
        )
        assert isinstance(response.json(), list)


def test_search_nonexistent_token(client):
    """T2.3.4: Verify searching for guaranteed non-existent token returns empty list []."""
    response = client.get("/api/v1/movies/search?q=xyznonexistenttoken99999999")
    assert response.status_code == 200
    movies = response.json()
    assert isinstance(movies, list)
    assert len(movies) == 0


def test_search_single_character(client):
    """T2.3.5: Verify single-character query works within requested limit."""
    response = client.get("/api/v1/movies/search?q=M&limit=5")
    assert response.status_code == 200
    movies = response.json()
    assert len(movies) <= 5
    for m in movies:
        assert "m" in m["title"].lower()


def test_search_case_insensitivity(client):
    """T2.3.6: Verify search is case-insensitive (MaTrIx matches The Matrix)."""
    r_lower = client.get("/api/v1/movies/search?q=matrix")
    r_upper = client.get("/api/v1/movies/search?q=MATRIX")
    r_mixed = client.get("/api/v1/movies/search?q=MaTrIx")

    assert r_lower.status_code == 200
    assert r_upper.status_code == 200
    assert r_mixed.status_code == 200

    titles_lower = [m["title"] for m in r_lower.json()]
    titles_upper = [m["title"] for m in r_upper.json()]
    titles_mixed = [m["title"] for m in r_mixed.json()]

    assert titles_lower == titles_upper == titles_mixed
    assert any("Matrix" in t for t in titles_lower)
