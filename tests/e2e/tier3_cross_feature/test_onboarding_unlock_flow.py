"""Tier 3: Cross-Feature Interactions - Mukesh Onboarding to Browse Unlock Lifecycle.

Verifies:
- Transition from 403 Forbidden to 200 OK after exact 6 ratings
- Ratings counter synchronization on profile endpoint
- Real-time personalization reflects genres of rated titles
- Browse gating reflects updated profile cold-start state
"""


def test_onboarding_unlock_progression(client):
    """T3.4.1: Verify step-by-step ratings count increment and unlock at exactly 6 ratings."""
    # Step 0: Initially 0 ratings
    prof0 = client.get("/api/v1/profiles/mukesh").json()
    assert prof0["ratings_count"] == 0
    assert prof0["is_cold_start"] is True
    assert client.get("/api/v1/profiles/mukesh/recommendations").status_code == 403

    # Steps 1 to 5: intermediate ratings remain gated
    starter_ids = [1, 2571, 589, 260, 318]
    for idx, mid in enumerate(starter_ids, start=1):
        res = client.post("/api/v1/profiles/mukesh/ratings", json={"movie_id": mid, "rating": 5.0})
        assert res.status_code == 200
        assert res.json()["ratings_count"] == idx
        assert res.json()["unlocked"] is False
        assert client.get("/api/v1/profiles/mukesh/recommendations").status_code == 403

    # Step 6: 6th rating unlocks profile
    res6 = client.post("/api/v1/profiles/mukesh/ratings", json={"movie_id": 527, "rating": 5.0})
    assert res6.status_code == 200
    assert res6.json()["ratings_count"] == 6
    assert res6.json()["unlocked"] is True

    # Step 7: Recommendations immediately accessible
    rec_res = client.get("/api/v1/profiles/mukesh/recommendations")
    assert rec_res.status_code == 200
    recs = rec_res.json()["items"]
    assert len(recs) > 0


def test_unlocked_recommendations_reflect_seeded_tastes(client):
    """T3.4.2: Verify unlocked recommendations reflect preferences of the 6 rated titles."""
    # Mukesh rates 6 Action/Sci-Fi titles with 5 stars
    action_scifi_ids = [2571, 589, 260, 1196, 1210, 1240]
    for mid in action_scifi_ids:
        client.post("/api/v1/profiles/mukesh/ratings", json={"movie_id": mid, "rating": 5.0})

    recs = client.get("/api/v1/profiles/mukesh/recommendations?limit=10").json()["items"]
    # Check that recommendations now favor Action or Sci-Fi
    action_or_scifi_count = sum(
        1 for r in recs if "Action" in r["genres"] or "Sci-Fi" in r["genres"]
    )
    assert action_or_scifi_count >= 5, (
        "Unlocked recommendations did not adapt to user's Action/Sci-Fi ratings"
    )
