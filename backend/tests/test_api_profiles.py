import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_profiles():
    response = client.get("/api/v1/profiles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3

    ids = [p["id"] for p in data]
    assert "neel" in ids
    assert "nitin" in ids
    assert "mukesh" in ids

    # Check fields
    neel = next(p for p in data if p["id"] == "neel")
    assert neel["name"] == "Neel"
    assert neel["ratings_count"] > 0
    assert neel["is_cold_start"] is False

    mukesh = next(p for p in data if p["id"] == "mukesh")
    assert mukesh["name"] == "Mukesh"
    assert mukesh["ratings_count"] == 0
    assert mukesh["is_cold_start"] is True


def test_get_profile_detail():
    response = client.get("/api/v1/profiles/neel")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "neel"
    assert data["user_idx"] == 2955

    res_not_found = client.get("/api/v1/profiles/unknown_profile_xyz")
    assert res_not_found.status_code == 404
