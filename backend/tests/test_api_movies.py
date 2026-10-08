import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_starter_grid_returns_24_movies():
    response = client.get("/api/v1/movies/starter")
    assert response.status_code == 200
    movies = response.json()
    assert len(movies) == 24
    for m in movies:
        assert "id" in m
        assert "title" in m
        assert "genres" in m
        assert isinstance(m["genres"], list)
        assert len(m["genres"]) > 0
        assert m["poster_path"] is not None


def test_search_movies():
    response = client.get("/api/v1/movies/search?q=Matrix")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0
    titles = [m["title"] for m in data["items"]]
    assert any("Matrix" in t for t in titles)


def test_get_movie_details():
    response = client.get("/api/v1/movies/1")
    assert response.status_code == 200
    movie = response.json()
    assert movie["id"] == 1
    assert "Toy Story" in movie["title"]
    assert movie["synopsis"] is not None
    assert movie["poster_path"] is not None
    assert movie["backdrop_path"] is not None

    res_404 = client.get("/api/v1/movies/99999999")
    assert res_404.status_code == 404
