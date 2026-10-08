"""Tier 4: Real-World Scenarios - Multi-Persona Catalog Audit & Isolation.

Verifies:
- Concurrent profile querying preserves isolated preference states
- Mutating Neel does not alter Nitin or Mukesh profiles or recommendations
- Profile switching in client retains proper user persona context
"""


def test_concurrent_persona_session_isolation(client):
    """T4.2.1: Verify mutating Neel does not bleed into Nitin's recommendations."""
    # Capture Nitin baseline recommendations
    nitin_baseline = client.get("/api/v1/profiles/nitin/recommendations?limit=10").json()["items"]
    nitin_baseline_ids = [it["movie_id"] for it in nitin_baseline]

    # Mutate Neel's profile by adding multiple high ratings for Animation / Comedy
    for mid in [1, 3, 4]:
        client.post("/api/v1/profiles/neel/ratings", json={"movie_id": mid, "rating": 5.0})

    # Verify Neel's ratings count increased
    neel_updated = client.get("/api/v1/profiles/neel").json()
    assert neel_updated["ratings_count"] >= 21

    # Verify Nitin remains completely untouched
    nitin_after = client.get("/api/v1/profiles/nitin").json()
    assert nitin_after["ratings_count"] == 14
    assert nitin_after["taste_cluster"] == "Drama / Romance"

    nitin_recs_after = client.get("/api/v1/profiles/nitin/recommendations?limit=10").json()["items"]
    nitin_ids_after = [it["movie_id"] for it in nitin_recs_after]

    assert nitin_ids_after == nitin_baseline_ids, (
        "Nitin recommendations leaked or altered by Neel mutations!"
    )


def test_mukesh_isolation_from_seeded_users(client):
    """T4.2.2: Verify Mukesh cold-start gating is not compromised by Neel or Nitin actions."""
    # Neel and Nitin are active
    client.get("/api/v1/profiles/neel/recommendations")
    client.get("/api/v1/profiles/nitin/recommendations")

    # Mukesh must remain strictly gated at 0 ratings
    mukesh_res = client.get("/api/v1/profiles/mukesh/recommendations")
    assert mukesh_res.status_code == 403
