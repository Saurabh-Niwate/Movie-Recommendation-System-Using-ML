"""Tier 1: Feature Coverage - User Profiles & Identity Management.

Verifies:
- Listing pre-seeded profiles (Neel, Nitin, Mukesh)
- Detailed profile inspection
- Cold-start flag assignment
- Non-existent profile error handling
- API routing aliasing
"""


def test_list_all_profiles(client):
    """T1.1.1: Verify listing profiles returns Neel, Nitin, Mukesh with schema conformity."""
    response = client.get("/api/v1/profiles")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    profiles = response.json()
    assert isinstance(profiles, list)
    assert len(profiles) == 3, f"Expected 3 demo profiles, found {len(profiles)}"

    profile_ids = {p["id"] for p in profiles}
    assert profile_ids == {"neel", "nitin", "mukesh"}

    for p in profiles:
        assert p.get("name")
        assert "avatar" in p
        assert "bio" in p
        assert "ratings_count" in p and isinstance(p["ratings_count"], int)
        assert "is_cold_start" in p and isinstance(p["is_cold_start"], bool)
        assert "taste_cluster" in p


def test_get_profile_neel(client):
    """T1.1.2: Verify Neel profile metadata: Action & Sci-Fi focus, pre-seeded ratings."""
    response = client.get("/api/v1/profiles/neel")
    assert response.status_code == 200
    p = response.json()
    assert p["id"] == "neel"
    assert p["name"] == "Neel"
    assert p["is_cold_start"] is False
    assert p["ratings_count"] >= 8
    assert "Action" in p["taste_cluster"] or "Sci-Fi" in p["taste_cluster"]


def test_get_profile_nitin(client):
    """T1.1.3: Verify Nitin profile metadata: Drama & Romance focus, pre-seeded ratings."""
    response = client.get("/api/v1/profiles/nitin")
    assert response.status_code == 200
    p = response.json()
    assert p["id"] == "nitin"
    assert p["name"] == "Nitin"
    assert p["is_cold_start"] is False
    assert p["ratings_count"] >= 7
    assert "Drama" in p["taste_cluster"] or "Romance" in p["taste_cluster"]


def test_get_profile_mukesh_cold_start(client):
    """T1.1.4: Verify Mukesh profile metadata: Cold start flag true, 0 ratings initially."""
    response = client.get("/api/v1/profiles/mukesh")
    assert response.status_code == 200
    p = response.json()
    assert p["id"] == "mukesh"
    assert p["name"] == "Mukesh"
    assert p["is_cold_start"] is True
    assert p["ratings_count"] == 0


def test_get_nonexistent_profile_returns_404(client):
    """T1.1.5: Verify querying invalid profile returns 404 Not Found."""
    response = client.get("/api/v1/profiles/nonexistent_agent_999")
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error
    assert "nonexistent_agent_999" in str(error["detail"])


def test_profile_endpoint_aliasing(client):
    """T1.1.6: Verify both /api/v1/profiles and /api/profiles return identical payloads."""
    r_v1 = client.get("/api/v1/profiles")
    r_alias = client.get("/api/profiles")
    assert r_v1.status_code == 200
    assert r_alias.status_code == 200
    assert r_v1.json() == r_alias.json()
