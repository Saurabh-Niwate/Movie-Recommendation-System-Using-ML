"""User genre clustering and demo profile extraction.

Uses KMeans clustering (k=4) on 18-dimensional normalized user genre distributions
to discover distinct taste segments and identify demo profiles:
- Neel (Action/Sci-Fi enthusiast, user_idx=2955)
- Nitin (Drama/Romance connoisseur, user_idx=2583)
- Mukesh (Cold-start viewer, 0 ratings)
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from recsys.config import PROCESSED_DIR, ARTIFACTS_DIR


def compute_user_genre_distributions(
    ratings_df: pd.DataFrame,
    movies_df: pd.DataFrame,
) -> Tuple[np.ndarray, List[str]]:
    """Compute 18-dimensional normalized genre distribution vector per user.
    
    Args:
        ratings_df: Ratings dataframe with user_idx, movie_id, rating.
        movies_df: Movies dataframe with movie_id, genres.
        
    Returns:
        Tuple of (user_genre_dist, sorted_genre_names).
    """
    # Extract unique genres
    all_genres = sorted(list({g for gl in movies_df["genres"] for g in gl}))
    genre2idx = {g: i for i, g in enumerate(all_genres)}
    n_genres = len(all_genres)
    n_users = int(ratings_df["user_idx"].max() + 1)

    movie_genres = dict(zip(movies_df["movie_id"], movies_df["genres"]))

    # Accumulate rating weights per user and genre
    user_genre_matrix = np.zeros((n_users, n_genres), dtype=np.float32)

    for row in ratings_df.itertuples():
        u = row.user_idx
        mid = row.movie_id
        r = float(row.rating)
        genres = movie_genres.get(mid, [])
        for g in genres:
            if g in genre2idx:
                user_genre_matrix[u, genre2idx[g]] += r

    # L1 normalize rows
    row_sums = user_genre_matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    user_genre_dist = user_genre_matrix / row_sums

    return user_genre_dist, all_genres


def cluster_user_profiles(
    ratings_df: pd.DataFrame,
    movies_df: pd.DataFrame,
    n_clusters: int = 4,
    random_state: int = 42,
) -> Tuple[KMeans, np.ndarray, np.ndarray, List[str]]:
    """Cluster user genre distributions into distinct preference clusters."""
    dist, genres = compute_user_genre_distributions(ratings_df, movies_df)
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(dist)
    return kmeans, labels, dist, genres


def generate_demo_profiles(
    ratings_df: Optional[pd.DataFrame] = None,
    movies_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Generate demo profile specifications for Neel, Nitin, and Mukesh."""
    if ratings_df is None:
        ratings_df = pd.read_parquet(PROCESSED_DIR / "ratings.parquet")
    if movies_df is None:
        movies_df = pd.read_parquet(PROCESSED_DIR / "movies.parquet")

    kmeans, labels, dist, genres = cluster_user_profiles(ratings_df, movies_df)

    neel_idx = 2955
    nitin_idx = 2583

    neel_cluster = int(labels[neel_idx])
    nitin_cluster = int(labels[nitin_idx])

    neel_count = int((ratings_df["user_idx"] == neel_idx).sum())
    nitin_count = int((ratings_df["user_idx"] == nitin_idx).sum())

    # Get Neel's user_id from ratings_df
    neel_uid_rows = ratings_df.loc[ratings_df["user_idx"] == neel_idx, "user_id"]
    neel_user_id = int(neel_uid_rows.iloc[0]) if len(neel_uid_rows) > 0 else 2956

    nitin_uid_rows = ratings_df.loc[ratings_df["user_idx"] == nitin_idx, "user_id"]
    nitin_user_id = int(nitin_uid_rows.iloc[0]) if len(nitin_uid_rows) > 0 else 2584

    profiles = {
        "neel": {
            "id": "neel",
            "name": "Neel",
            "user_idx": neel_idx,
            "user_id": neel_user_id,
            "genres": ["Action", "Sci-Fi"],
            "cluster": neel_cluster,
            "avatar": "/avatars/neel.png",
            "bio": "Action & Sci-Fi enthusiast",
            "ratings_count": neel_count,
            "is_cold_start": False,
        },
        "nitin": {
            "id": "nitin",
            "name": "Nitin",
            "user_idx": nitin_idx,
            "user_id": nitin_user_id,
            "genres": ["Drama", "Romance"],
            "cluster": nitin_cluster,
            "avatar": "/avatars/nitin.png",
            "bio": "Drama & Romance connoisseur",
            "ratings_count": nitin_count,
            "is_cold_start": False,
        },
        "mukesh": {
            "id": "mukesh",
            "name": "Mukesh",
            "user_idx": None,
            "user_id": None,
            "genres": [],
            "cluster": None,
            "avatar": "/avatars/mukesh.png",
            "bio": "New viewer exploring cinema",
            "ratings_count": 0,
            "is_cold_start": True,
        },
    }
    return profiles


def export_profiles(output_path: Optional[Path] = None) -> Path:
    """Generate and write profiles to artifacts/v1/profiles.json."""
    if output_path is None:
        output_path = ARTIFACTS_DIR / "profiles.json"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    profiles = generate_demo_profiles()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)

    print(f"[recsys] Exported demo profiles to {output_path}")
    return output_path


if __name__ == "__main__":
    export_profiles()
