import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_mukesh_cold_start_gating_forbidden():
    """Verify that Mukesh with <6 ratings returns 403 Forbidden across recommendation endpoints."""
    # 1. Profile recommendations
    res1 = client.get("/api/v1/profiles/mukesh/recommendations")
    assert res1.status_code == 403
    assert "Cold start profile requires at least 6 ratings" in res1.json()["detail"]

    # 2. General recommendations
    res2 = client.get("/api/v1/recommendations?profile_id=mukesh")
    assert res2.status_code == 403
    assert "Cold start profile requires at least 6 ratings" in res2.json()["detail"]

    # 3. Billboard
    res3 = client.get("/api/v1/recommendations/billboard?profile_id=mukesh")
    assert res3.status_code == 403
    assert "Cold start profile requires at least 6 ratings" in res3.json()["detail"]

    # 4. Because you liked
    res4 = client.get("/api/v1/recommendations/because-you-liked?profile_id=mukesh")
    assert res4.status_code == 403
    assert "Cold start profile requires at least 6 ratings" in res4.json()["detail"]


def test_distinct_recommendations_neel_vs_nitin():
    """Verify that Neel (Action/Sci-Fi) and Nitin (Drama/Romance) receive distinctly different recommendations."""
    res_neel = client.get("/api/v1/profiles/neel/recommendations?model=funk_svd&limit=10")
    assert res_neel.status_code == 200
    neel_items = res_neel.json()
    assert len(neel_items) == 10

    res_nitin = client.get("/api/v1/profiles/nitin/recommendations?model=funk_svd&limit=10")
    assert res_nitin.status_code == 200
    nitin_items = res_nitin.json()
    assert len(nitin_items) == 10

    neel_ids = {m["id"] for m in neel_items}
    nitin_ids = {m["id"] for m in nitin_items}

    # Verify distinct recommendations with minimal overlap
    overlap = neel_ids.intersection(nitin_ids)
    assert len(overlap) <= 2, f"Overlap between Neel and Nitin too high: {overlap}"

    # Verify genre differences
    neel_genres = [g for m in neel_items for g in m["genres"]]
    nitin_genres = [g for m in nitin_items for g in m["genres"]]

    assert any(g in ["Action", "Sci-Fi", "Thriller"] for g in neel_genres)
    assert any(g in ["Drama", "Romance", "Comedy"] for g in nitin_genres)


def test_model_toggle_funk_svd_vs_item_knn():
    """Verify that recommendations can be generated via both Funk-SVD and Item-KNN."""
    res_svd = client.get("/api/v1/profiles/neel/recommendations?model=funk_svd&limit=10")
    assert res_svd.status_code == 200
    svd_data = res_svd.json()
    assert svd_data[0]["algorithm"] == "Funk-SVD"

    res_knn = client.get("/api/v1/profiles/neel/recommendations?model=item_knn&limit=10")
    assert res_knn.status_code == 200
    knn_data = res_knn.json()
    assert knn_data[0]["algorithm"] == "Item-KNN"


def test_billboard_hero_recommendation():
    """Verify billboard returns hero movie for un-gated profiles."""
    res = client.get("/api/v1/recommendations/billboard?profile_id=neel")
    assert res.status_code == 200
    hero = res.json()
    assert "id" in hero
    assert "title" in hero
    assert hero["match_percent"] >= 50


def test_because_you_liked_endpoint():
    """Verify 'Because you liked' returns top movie and KNN similar movies."""
    res = client.get("/api/v1/recommendations/because-you-liked?profile_id=neel")
    assert res.status_code == 200
    data = res.json()
    assert "source_movie" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0


def test_also_watched_endpoint():
    """Verify 'Users also watched' returns association rules lift items."""
    # Matrix movie id is 2571
    res = client.get("/api/v1/recommendations/also-watched/2571?limit=5")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    if items:
        assert "lift" in items[0]
        assert "cooccurrence" in items[0]


def test_genre_carousels_endpoint():
    """Verify genre carousels return multiple genre rows."""
    res = client.get("/api/v1/recommendations/genres")
    assert res.status_code == 200
    carousels = res.json()
    assert len(carousels) >= 4
    genre_names = [c["genre"] for c in carousels]
    assert "Action" in genre_names
    assert "Drama" in genre_names
