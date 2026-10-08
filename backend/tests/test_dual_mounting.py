import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dual_mounting_profiles():
    res_v1 = client.get("/api/v1/profiles")
    res_raw = client.get("/api/profiles")
    assert res_v1.status_code == 200
    assert res_raw.status_code == 200
    assert res_v1.json() == res_raw.json()


def test_dual_mounting_movies():
    res_v1 = client.get("/api/v1/movies/starter")
    res_raw = client.get("/api/movies/starter")
    assert res_v1.status_code == 200
    assert res_raw.status_code == 200
    assert len(res_v1.json()) == len(res_raw.json())


def test_dual_mounting_recommendations():
    res_v1 = client.get("/api/v1/recommendations/billboard?profile_id=neel")
    res_raw = client.get("/api/recommendations/billboard?profile_id=neel")
    assert res_v1.status_code == 200
    assert res_raw.status_code == 200
    assert res_v1.json()["id"] == res_raw.json()["id"]


def test_dual_mounting_model_lab():
    res_v1 = client.get("/api/v1/model-lab/leaderboard")
    res_raw = client.get("/api/model-lab/leaderboard")
    assert res_v1.status_code == 200
    assert res_raw.status_code == 200
    assert res_v1.json() == res_raw.json()
