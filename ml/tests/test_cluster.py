"""Unit tests for user genre distribution clustering and demo profiles."""
import pandas as pd
import numpy as np
import pytest

from recsys.profiles.cluster import (
    compute_user_genre_distributions,
    cluster_user_profiles,
    generate_demo_profiles,
)


@pytest.fixture
def mini_profiles_data():
    """Create mini ratings and movies dataframes with genre memberships."""
    movies_df = pd.DataFrame({
        "movie_id": [1, 2, 3, 4],
        "genres": [["Action", "Sci-Fi"], ["Action"], ["Drama", "Romance"], ["Drama"]],
    })
    # User 0: Action/Sci-Fi fan (rates movies 1 and 2 high)
    # User 1: Drama/Romance fan (rates movies 3 and 4 high)
    # User 2: Action fan
    # User 3: Drama fan
    ratings_df = pd.DataFrame({
        "user_idx": [0, 0, 1, 1, 2, 3],
        "user_id": [101, 101, 102, 102, 103, 104],
        "movie_id": [1, 2, 3, 4, 1, 3],
        "rating": [5.0, 5.0, 5.0, 4.0, 4.0, 4.0],
    })
    return ratings_df, movies_df


def test_compute_user_genre_distributions(mini_profiles_data):
    """Test normalized genre distributions sum to 1."""
    ratings_df, movies_df = mini_profiles_data
    dist, genres = compute_user_genre_distributions(ratings_df, movies_df)

    assert dist.shape[0] == 4  # 4 users
    assert len(genres) == 4    # Action, Drama, Romance, Sci-Fi
    # Each user's genre distribution should sum to 1.0
    row_sums = dist.sum(axis=1)
    np.testing.assert_allclose(row_sums, 1.0, atol=1e-5)

    # User 0 should have 0 weight in Drama and Romance
    drama_idx = genres.index("Drama")
    romance_idx = genres.index("Romance")
    assert dist[0, drama_idx] == 0.0
    assert dist[0, romance_idx] == 0.0


def test_demo_profiles_definitions():
    """Verify demo profiles specification for Neel, Nitin, and Mukesh."""
    profiles = generate_demo_profiles()

    assert "neel" in profiles
    assert "nitin" in profiles
    assert "mukesh" in profiles

    neel = profiles["neel"]
    nitin = profiles["nitin"]
    mukesh = profiles["mukesh"]

    # Neel preferences
    assert neel["user_idx"] == 2955
    assert "Action" in neel["genres"]
    assert "Sci-Fi" in neel["genres"]
    assert neel["is_cold_start"] is False
    assert neel["ratings_count"] > 0

    # Nitin preferences
    assert nitin["user_idx"] == 2583
    assert "Drama" in nitin["genres"]
    assert "Romance" in nitin["genres"]
    assert nitin["is_cold_start"] is False
    assert nitin["ratings_count"] > 0

    # Mukesh cold-start
    assert mukesh["user_idx"] is None
    assert mukesh["is_cold_start"] is True
    assert mukesh["ratings_count"] == 0
    assert len(mukesh["genres"]) == 0
