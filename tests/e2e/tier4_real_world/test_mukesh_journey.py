"""Tier 4: Real-World Scenarios - Mukesh Onboarding to Active Streaming Journey.

End-to-end user journey simulation replicating the Furtado & Singh (2020) workflow:
1. User Selects Mukesh Profile from Profile Picker.
2. User Attempts to Access Personalized Browse Page -> Blocked by Onboarding Gate (403).
3. User Opens Onboarding Screen and Explores 24 Starter Movies Grid.
4. User Searches Catalog for Specific Title.
5. User Rates 6 Movies Sequentially (observing visual counter 1/6 .. 6/6).
6. Unlock Condition Triggers: Button Enabled, Recommendations Unlocked.
7. User Enters Browse Page: Hero Billboard and Carousels Render Personalized Titles.
8. User Opens Title Detail Modal and Submits 7th Rating: Instant Closed-Form Fold-In.
"""


def test_mukesh_full_onboarding_to_streaming_journey(client):
    """T4.1: Simulate complete subscriber lifecycle for new member Mukesh."""
    # Step 1: User queries profiles (Profile Picker "Who's watching?")
    profiles_res = client.get("/api/v1/profiles")
    assert profiles_res.status_code == 200
    mukesh = next(p for p in profiles_res.json() if p["id"] == "mukesh")
    assert mukesh["ratings_count"] == 0
    assert mukesh["is_cold_start"] is True

    # Step 2: Attempting to browse recommendations is blocked
    browse_res = client.get("/api/v1/profiles/mukesh/recommendations")
    assert browse_res.status_code == 403
    assert "at least 6 ratings" in browse_res.json()["detail"].lower()

    # Step 3: Fetch starter catalog grid (24 popular movies)
    starter_res = client.get("/api/v1/movies/starter")
    assert starter_res.status_code == 200
    starter_movies = starter_res.json()
    assert len(starter_movies) == 24

    # Step 4: Search catalog for a specific movie of interest
    search_res = client.get("/api/v1/movies/search?q=Matrix")
    assert search_res.status_code == 200
    search_movies = search_res.json()
    assert len(search_movies) > 0
    matrix_id = search_movies[0]["movie_id"]

    # Step 5: Rate 5 movies from starter grid (progress 1..5, still locked)
    for idx, m in enumerate(starter_movies[:5], start=1):
        rate_res = client.post(
            "/api/v1/profiles/mukesh/ratings",
            json={"movie_id": m["movie_id"], "rating": 4.5},
        )
        assert rate_res.status_code == 200
        assert rate_res.json()["ratings_count"] == idx
        assert rate_res.json()["unlocked"] is False

        # Verify still blocked at count < 6
        assert client.get("/api/v1/profiles/mukesh/recommendations").status_code == 403

    # Step 6: Rate 6th movie (The Matrix found via search) -> triggers unlock!
    unlock_res = client.post(
        "/api/v1/profiles/mukesh/ratings",
        json={"movie_id": matrix_id, "rating": 5.0},
    )
    assert unlock_res.status_code == 200
    assert unlock_res.json()["ratings_count"] == 6
    assert unlock_res.json()["unlocked"] is True

    # Step 7: Browse page now opens successfully
    browse_unlocked = client.get("/api/v1/profiles/mukesh/recommendations?limit=10")
    assert browse_unlocked.status_code == 200
    recs = browse_unlocked.json()["items"]
    assert len(recs) == 10

    # Step 8: User opens title detail modal for first recommendation and rates it
    target_rec = recs[0]
    detail_res = client.get(f"/api/v1/movies/{target_rec['movie_id']}")
    assert detail_res.status_code == 200
    assert detail_res.json()["movie_id"] == target_rec["movie_id"]

    # Rate 7th movie
    seventh_res = client.post(
        "/api/v1/profiles/mukesh/ratings",
        json={"movie_id": target_rec["movie_id"], "rating": 4.0},
    )
    assert seventh_res.status_code == 200
    assert seventh_res.json()["ratings_count"] == 7
    assert seventh_res.json()["fold_in_time_ms"] < 100.0
