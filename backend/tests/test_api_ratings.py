import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.profile import Profile
from app.models.rating import Rating

client = TestClient(app)


def test_rating_submission_and_online_fold_in_unfolding():
    """Verify progressive rating submission, <50ms fold-in, cold-start unlocking, and cache invalidation."""
    db = SessionLocal()
    try:
        # Pre-condition: Mukesh starts with 0 ratings
        db.query(Rating).filter_by(profile_id="mukesh").delete()
        mukesh = db.query(Profile).filter_by(id="mukesh").first()
        mukesh.ratings_count = 0
        mukesh.is_cold_start = True
        db.commit()

        # Step 1: verify 403 Forbidden before ratings
        res_gated = client.get("/api/v1/profiles/mukesh/recommendations")
        assert res_gated.status_code == 403

        # Step 2: Rate 5 movies (1 to 5)
        starter_movies = [1, 2, 3, 4, 5]
        for i, mid in enumerate(starter_movies):
            res_rate = client.post(
                "/api/v1/profiles/mukesh/ratings",
                json={"movie_id": mid, "rating": 4.5},
            )
            assert res_rate.status_code == 200
            data = res_rate.json()
            assert data["status"] == "ok"
            assert data["ratings_count"] == i + 1
            assert data["unlocked"] is False
            assert data["fold_in_ms"] < 50.0  # Real-time online fold-in < 50ms!

            # Still gated at count < 6
            res_still_gated = client.get("/api/v1/profiles/mukesh/recommendations")
            assert res_still_gated.status_code == 403

        # Step 3: Rate 6th movie (triggers cold-start unlock)
        res_unlock = client.post(
            "/api/v1/profiles/mukesh/ratings",
            json={"movie_id": 6, "rating": 5.0},
        )
        assert res_unlock.status_code == 200
        unlock_data = res_unlock.json()
        assert unlock_data["ratings_count"] == 6
        assert unlock_data["unlocked"] is True
        assert unlock_data["fold_in_ms"] < 50.0

        # Step 4: Verify recommendations endpoint is unlocked and returns personalized picks
        res_success = client.get("/api/v1/profiles/mukesh/recommendations")
        assert res_success.status_code == 200
        recs = res_success.json()
        assert len(recs) == 20

        # Verify rated movies are not recommended
        rec_ids = {r["id"] for r in recs}
        for rated_id in [1, 2, 3, 4, 5, 6]:
            assert rated_id not in rec_ids

        # Step 5: Test general POST /api/v1/ratings endpoint
        res_gen = client.post(
            "/api/v1/ratings",
            json={"profile_id": "mukesh", "movie_id": 7, "rating": 4.0},
        )
        assert res_gen.status_code == 200
        assert res_gen.json()["ratings_count"] == 7

        # Step 6: Verify GET ratings for profile
        res_list = client.get("/api/v1/profiles/mukesh/ratings")
        assert res_list.status_code == 200
        assert len(res_list.json()) == 7

    finally:
        # Cleanup test ratings for Mukesh to keep DB deterministic
        db.query(Rating).filter_by(profile_id="mukesh").delete()
        mukesh = db.query(Profile).filter_by(id="mukesh").first()
        if mukesh:
            mukesh.ratings_count = 0
            mukesh.is_cold_start = True
            db.commit()
        db.close()
