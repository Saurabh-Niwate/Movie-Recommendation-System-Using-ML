import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.tmdb import (
    TMDBService,
    generate_svg_poster,
    generate_svg_backdrop,
    generate_deterministic_synopsis,
    generate_deterministic_credits,
)

client = TestClient(app)



def test_generate_svg_poster():
    """Verify SVG poster generation output format, size, and content."""
    uri = generate_svg_poster("The Matrix", 1999, ["Action", "Sci-Fi"], 1)
    assert uri.startswith("data:image/svg+xml;base64,")
    # Base64 string should be substantial
    assert len(uri) > 500


def test_generate_svg_backdrop():
    """Verify SVG backdrop generation output format and dimensions."""
    uri = generate_svg_backdrop("Interstellar", 2014, ["Sci-Fi", "Drama"], 2)
    assert uri.startswith("data:image/svg+xml;base64,")
    assert len(uri) > 500


def test_generate_deterministic_synopsis():
    """Verify deterministic synopsis includes title, year, and genre details."""
    synopsis = generate_deterministic_synopsis("Inception", 2010, ["Action", "Sci-Fi"], 3)
    assert "Inception" in synopsis
    assert "2010" in synopsis
    assert "Action, Sci-Fi" in synopsis


def test_generate_deterministic_credits():
    """Verify deterministic credits produces director, cast list, runtime."""
    credits_info = generate_deterministic_credits(["Action"], 4)
    assert "director" in credits_info
    assert len(credits_info["director"]) > 0
    assert "cast" in credits_info
    assert isinstance(credits_info["cast"], list)
    assert len(credits_info["cast"]) >= 3
    assert 90 <= credits_info["runtime"] <= 180


def test_tmdb_service_offline_mode():
    """Verify TMDBService provides fallback metadata when API key is offline/placeholder."""
    service = TMDBService(api_key="apikey")
    assert service.is_offline is True

    # Offline search
    search_results = service.search_movies_sync("Matrix", year=1999)
    assert len(search_results) == 1
    assert search_results[0]["title"] == "Matrix"

    # Offline details
    details = service.get_movie_details_sync(2571)
    assert details["tmdb_id"] == 2571
    assert "poster_path" in details
    assert details["poster_path"].startswith("data:image/svg+xml;base64,")

    # Offline enrichment
    enriched = service.enrich_movie("Gladiator", 2000, ["Action", "Drama"], 10)
    assert enriched["title"] == "Gladiator"
    assert enriched["year"] == 2000
    assert enriched["poster_path"].startswith("data:image/svg+xml;base64,")
    assert enriched["backdrop_path"].startswith("data:image/svg+xml;base64,")


def test_tmdb_read_access_token_bearer_headers():
    """Verify TMDBService creates Authorization: Bearer <token> headers with Read Access Token."""
    dummy_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeak"
    service = TMDBService(read_token=dummy_jwt)
    assert service.is_offline is False
    headers = service._get_headers()
    assert headers["Authorization"] == f"Bearer {dummy_jwt}"
    assert headers["accept"] == "application/json"


def test_tmdb_router_endpoints():
    """Test /api/v1/tmdb and /api/tmdb status and fallback endpoints."""
    # Test status endpoint
    resp = client.get("/api/v1/tmdb/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "is_offline" in data
    assert "auth_mode" in data

    # Test dual-mounting on /api/tmdb/status
    resp_dual = client.get("/api/tmdb/status")
    assert resp_dual.status_code == 200
    assert resp_dual.json()["auth_mode"] == data["auth_mode"]

    # Test search endpoint
    search_resp = client.get("/api/v1/tmdb/search?query=Inception&year=2010")
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) >= 1
    assert "title" in results[0]

    # Test movie details endpoint
    movie_resp = client.get("/api/v1/tmdb/movie/27205")
    assert movie_resp.status_code == 200
    m_data = movie_resp.json()
    assert m_data["tmdb_id"] == 27205

