"""High-fidelity contract-compliant mock application for CineMatch E2E testing.

Implements all endpoints and interface contracts specified in PROJECT.md:
- /api/v1/profiles, /api/v1/profiles/{id}
- /api/v1/profiles/{id}/recommendations
- /api/v1/recommendations/billboard
- /api/v1/recommendations/because-you-liked
- /api/v1/recommendations/also-watched/{movie_id}
- /api/v1/movies/starter
- /api/v1/movies/search
- /api/v1/movies/{id}
- /api/v1/profiles/{id}/ratings
- /api/v1/model-lab/leaderboard
- /api/v1/model-lab/convergence
- /api/v1/model-lab/compare
- /api/v1/model-lab/explain
- /api/v1/profiles/reset
"""

from __future__ import annotations

import copy
import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

# Load real MovieLens catalog if available
ROOT_DIR = Path(__file__).resolve().parents[3]
PARQUET_PATH = ROOT_DIR / "data" / "processed" / "movies.parquet"

CATALOG: list[dict[str, Any]] = []

if PARQUET_PATH.exists():
    try:
        df = pd.read_parquet(PARQUET_PATH)
        for _, row in df.iterrows():
            genres_val = row["genres"]
            if hasattr(genres_val, "__iter__") and not isinstance(genres_val, (str, bytes)):
                genres = [str(g).strip() for g in genres_val if str(g).strip()]
            elif isinstance(genres_val, str):
                genres = [g.strip() for g in genres_val.split("|") if g.strip()]
            else:
                genres = []

            year = int(row["year"]) if pd.notna(row["year"]) else 1990
            CATALOG.append(
                {
                    "movie_id": int(row["movie_id"]),
                    "item_idx": int(row["item_idx"])
                    if pd.notna(row.get("item_idx"))
                    else int(row["movie_id"]),
                    "title": str(row["title"]),
                    "year": year,
                    "genres": genres,
                    "synopsis": f"A compelling film exploring {', '.join(genres) if genres else 'dramatic'} themes.",
                    "director": "Acclaimed Director",
                    "cast": ["Lead Actor", "Supporting Star"],
                    "poster_path": f"/posters/{row['movie_id']}.jpg",
                    "backdrop_path": f"/backdrops/{row['movie_id']}.jpg",
                    "vote_average": 4.2,
                    "vote_count": 1250,
                    "runtime": 124,
                }
            )
    except (OSError, ValueError, KeyError):
        CATALOG = []

if not CATALOG:
    # Deterministic fallback sample catalog if parquet cannot be read
    CATALOG = [
        {
            "movie_id": 1,
            "item_idx": 0,
            "title": "Toy Story",
            "year": 1995,
            "genres": ["Animation", "Children's", "Comedy"],
            "synopsis": "A cowboy doll is profoundly threatened...",
            "director": "John Lasseter",
            "cast": ["Tom Hanks", "Tim Allen"],
            "poster_path": "/posters/1.jpg",
            "backdrop_path": "/backdrops/1.jpg",
            "vote_average": 4.1,
            "vote_count": 2077,
            "runtime": 81,
        },
        {
            "movie_id": 2571,
            "item_idx": 1,
            "title": "The Matrix",
            "year": 1999,
            "genres": ["Action", "Sci-Fi"],
            "synopsis": "A computer hacker learns about reality...",
            "director": "Lana Wachowski",
            "cast": ["Keanu Reeves", "Laurence Fishburne"],
            "poster_path": "/posters/2571.jpg",
            "backdrop_path": "/backdrops/2571.jpg",
            "vote_average": 4.3,
            "vote_count": 2590,
            "runtime": 136,
        },
        {
            "movie_id": 589,
            "item_idx": 2,
            "title": "Terminator 2: Judgment Day",
            "year": 1991,
            "genres": ["Action", "Sci-Fi", "Thriller"],
            "synopsis": "A cyborg is sent back in time...",
            "director": "James Cameron",
            "cast": ["Arnold Schwarzenegger", "Linda Hamilton"],
            "poster_path": "/posters/589.jpg",
            "backdrop_path": "/backdrops/589.jpg",
            "vote_average": 4.2,
            "vote_count": 2649,
            "runtime": 137,
        },
        {
            "movie_id": 260,
            "item_idx": 3,
            "title": "Star Wars: Episode IV - A New Hope",
            "year": 1977,
            "genres": ["Action", "Adventure", "Sci-Fi"],
            "synopsis": "Luke Skywalker joins forces with a Jedi Knight...",
            "director": "George Lucas",
            "cast": ["Mark Hamill", "Harrison Ford"],
            "poster_path": "/posters/260.jpg",
            "backdrop_path": "/backdrops/260.jpg",
            "vote_average": 4.4,
            "vote_count": 2991,
            "runtime": 121,
        },
        {
            "movie_id": 318,
            "item_idx": 4,
            "title": "The Shawshank Redemption",
            "year": 1994,
            "genres": ["Drama"],
            "synopsis": "Two imprisoned men bond over a number of years...",
            "director": "Frank Darabont",
            "cast": ["Tim Robbins", "Morgan Freeman"],
            "poster_path": "/posters/318.jpg",
            "backdrop_path": "/backdrops/318.jpg",
            "vote_average": 4.5,
            "vote_count": 2227,
            "runtime": 142,
        },
        {
            "movie_id": 527,
            "item_idx": 5,
            "title": "Schindler's List",
            "year": 1993,
            "genres": ["Drama", "War"],
            "synopsis": "In German-occupied Poland during World War II...",
            "director": "Steven Spielberg",
            "cast": ["Liam Neeson", "Ben Kingsley"],
            "poster_path": "/posters/527.jpg",
            "backdrop_path": "/backdrops/527.jpg",
            "vote_average": 4.5,
            "vote_count": 2304,
            "runtime": 195,
        },
        {
            "movie_id": 1196,
            "item_idx": 6,
            "title": "Star Wars: Episode V - The Empire Strikes Back",
            "year": 1980,
            "genres": ["Action", "Adventure", "Sci-Fi"],
            "synopsis": "After the Rebels are brutally overpowered by the Empire...",
            "director": "Irvin Kershner",
            "cast": ["Mark Hamill", "Harrison Ford"],
            "poster_path": "/posters/1196.jpg",
            "backdrop_path": "/backdrops/1196.jpg",
            "vote_average": 4.3,
            "vote_count": 2990,
            "runtime": 124,
        },
        {
            "movie_id": 1721,
            "item_idx": 7,
            "title": "Titanic",
            "year": 1997,
            "genres": ["Drama", "Romance"],
            "synopsis": "A seventeen-year-old aristocrat falls in love with a kind but poor artist...",
            "director": "James Cameron",
            "cast": ["Leonardo DiCaprio", "Kate Winslet"],
            "poster_path": "/posters/1721.jpg",
            "backdrop_path": "/backdrops/1721.jpg",
            "vote_average": 4.0,
            "vote_count": 1546,
            "runtime": 194,
        },
        {
            "movie_id": 912,
            "item_idx": 8,
            "title": "Casablanca",
            "year": 1942,
            "genres": ["Drama", "Romance", "War"],
            "synopsis": "A cynical expatriate American cafe owner struggles...",
            "director": "Michael Curtiz",
            "cast": ["Humphrey Bogart", "Ingrid Bergman"],
            "poster_path": "/posters/912.jpg",
            "backdrop_path": "/backdrops/912.jpg",
            "vote_average": 4.4,
            "vote_count": 1669,
            "runtime": 102,
        },
        {
            "movie_id": 356,
            "item_idx": 9,
            "title": "Forrest Gump",
            "year": 1994,
            "genres": ["Comedy", "Drama", "Romance"],
            "synopsis": "The history of the United States from the 1950s to the '70s...",
            "director": "Robert Zemeckis",
            "cast": ["Tom Hanks", "Robin Wright"],
            "poster_path": "/posters/356.jpg",
            "backdrop_path": "/backdrops/356.jpg",
            "vote_average": 4.1,
            "vote_count": 2194,
            "runtime": 142,
        },
    ]

MOVIE_LOOKUP = {m["movie_id"]: m for m in CATALOG}

# Pre-seeded profile blueprints
INITIAL_PROFILES: dict[str, dict[str, Any]] = {
    "neel": {
        "id": "neel",
        "name": "Neel",
        "avatar": "/avatars/neel.png",
        "bio": "Action & Sci-Fi Enthusiast",
        "user_idx": 2955,
        "is_cold_start": False,
        "taste_cluster": "Action / Sci-Fi",
        "ratings_count": 18,
        "ratings": {
            2571: 5.0,  # The Matrix
            589: 5.0,  # Terminator 2
            260: 4.5,  # Star Wars IV
            1196: 4.5,  # Star Wars V
            1210: 4.0,  # Star Wars VI
            1240: 4.5,  # The Terminator
            480: 4.0,  # Jurassic Park
            1580: 4.0,  # Men in Black
            541: 4.5,  # Blade Runner
            1036: 4.0,  # Die Hard
            1200: 4.5,  # Aliens
            1214: 4.5,  # Alien
            1270: 4.5,  # Back to the Future
            1527: 4.0,  # The Fifth Element
            1573: 4.0,  # Face/Off
            1610: 4.0,  # The Hunt for Red October
            1653: 4.0,  # Gattaca
            1682: 4.0,  # The Truman Show
        },
    },
    "nitin": {
        "id": "nitin",
        "name": "Nitin",
        "avatar": "/avatars/nitin.png",
        "bio": "Drama & Romance Connoisseur",
        "user_idx": 2583,
        "is_cold_start": False,
        "taste_cluster": "Drama / Romance",
        "ratings_count": 14,
        "ratings": {
            318: 5.0,  # Shawshank Redemption
            527: 5.0,  # Schindler's List
            1721: 4.5,  # Titanic
            912: 5.0,  # Casablanca
            356: 4.5,  # Forrest Gump
            1193: 4.5,  # One Flew Over the Cuckoo's Nest
            1221: 5.0,  # The Godfather Part II
            1945: 4.5,  # On the Waterfront
            1968: 4.5,  # Breakfast at Tiffany's
            2028: 5.0,  # Saving Private Ryan
            2064: 4.5,  # Roger & Me
            2324: 4.5,  # Life Is Beautiful
            2396: 4.5,  # Shakespeare in Love
            2572: 4.0,  # 10 Things I Hate About You
        },
    },
    "mukesh": {
        "id": "mukesh",
        "name": "Mukesh",
        "avatar": "/avatars/mukesh.png",
        "bio": "New Cinephile (Cold Start)",
        "user_idx": None,
        "is_cold_start": True,
        "taste_cluster": "Cold Start",
        "ratings_count": 0,
        "ratings": {},
    },
}


class RatingSubmission(BaseModel):
    movie_id: int
    rating: float = Field(..., ge=1.0, le=5.0)


def create_contract_app() -> FastAPI:
    """Create FastAPI application fulfilling CineMatch E2E contracts."""
    app = FastAPI(title="CineMatch E2E Contract Service", version="1.0.0")

    # Mutable state for tests
    state_profiles: dict[str, dict[str, Any]] = copy.deepcopy(INITIAL_PROFILES)

    @app.post("/api/v1/profiles/reset")
    def reset_profiles() -> dict[str, str]:
        nonlocal state_profiles
        state_profiles = copy.deepcopy(INITIAL_PROFILES)
        return {"status": "reset_successful"}

    @app.get("/api/v1/profiles")
    @app.get("/api/profiles")
    def list_profiles() -> list[dict[str, Any]]:
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "avatar": p["avatar"],
                "bio": p["bio"],
                "ratings_count": len(p["ratings"]) if p["id"] == "mukesh" else p["ratings_count"],
                "is_cold_start": len(p["ratings"]) < 6
                if p["id"] == "mukesh"
                else p["is_cold_start"],
                "taste_cluster": p["taste_cluster"],
            }
            for p in state_profiles.values()
        ]

    @app.get("/api/v1/profiles/{profile_id}")
    @app.get("/api/profiles/{profile_id}")
    def get_profile(profile_id: str) -> dict[str, Any]:
        if profile_id not in state_profiles:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
        p = state_profiles[profile_id]
        current_count = len(p["ratings"]) if profile_id == "mukesh" else p["ratings_count"]
        is_cold = (current_count < 6) if profile_id == "mukesh" else p["is_cold_start"]
        return {
            "id": p["id"],
            "name": p["name"],
            "avatar": p["avatar"],
            "bio": p["bio"],
            "ratings_count": current_count,
            "is_cold_start": is_cold,
            "taste_cluster": p["taste_cluster"],
        }

    @app.get("/api/v1/movies/starter")
    @app.get("/api/movies/starter")
    def get_starter_movies() -> list[dict[str, Any]]:
        # Return 24 diverse popular movies
        return CATALOG[:24]

    @app.get("/api/v1/movies/search")
    @app.get("/api/movies/search")
    def search_movies(
        q: str | None = Query(None),
        genre: str | None = Query(None),
        limit: int = Query(20, ge=1, le=100),
    ) -> list[dict[str, Any]]:
        results = CATALOG
        if genre:
            genre_lower = genre.lower()
            results = [m for m in results if any(g.lower() == genre_lower for g in m["genres"])]
        if q:
            q_clean = q.strip()
            if not q_clean:
                return results[:limit]
            # Safe regex escape to avoid adversarial crashing
            pattern = re.escape(q_clean)
            results = [m for m in results if re.search(pattern, m["title"], re.IGNORECASE)]
        return results[:limit]

    @app.get("/api/v1/movies/{movie_id}")
    @app.get("/api/movies/{movie_id}")
    def get_movie_detail(movie_id: int) -> dict[str, Any]:
        if movie_id not in MOVIE_LOOKUP:
            raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found")
        return MOVIE_LOOKUP[movie_id]

    @app.get("/api/v1/profiles/{profile_id}/recommendations")
    @app.get("/api/profiles/{profile_id}/recommendations")
    def get_recommendations(
        profile_id: str,
        model: str = Query("funk_svd", pattern="^(funk_svd|item_knn|popularity)$"),
        limit: int = Query(20, ge=1, le=100),
    ) -> dict[str, Any]:
        if profile_id not in state_profiles:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")

        p = state_profiles[profile_id]
        current_ratings = p["ratings"]
        current_count = len(current_ratings) if profile_id == "mukesh" else p["ratings_count"]

        # Enforce cold start gating per Furtado & Singh (2020)
        if profile_id == "mukesh" and current_count < 6:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cold start profile requires at least 6 ratings. Currently rated: {current_count}/6.",
            )

        # Generate personalized recommendations
        scored_items: list[dict[str, Any]] = []

        if profile_id == "neel":
            preferred_genres = {"Action", "Sci-Fi", "Adventure", "Thriller"}
        elif profile_id == "nitin":
            preferred_genres = {"Drama", "Romance", "War"}
        else:
            # Mukesh unlocked: derive preference from user's current ratings
            genre_weights: dict[str, float] = {}
            for mid, r in current_ratings.items():
                m = MOVIE_LOOKUP.get(mid)
                if m:
                    for g in m["genres"]:
                        genre_weights[g] = genre_weights.get(g, 0.0) + (r - 2.5)
            preferred_genres = {g for g, w in genre_weights.items() if w > 0}
            if not preferred_genres:
                preferred_genres = {"Drama", "Action", "Comedy"}

        for m in CATALOG:
            # Exclude already rated
            if m["movie_id"] in current_ratings:
                continue

            genre_overlap = len(set(m["genres"]).intersection(preferred_genres))
            is_match = genre_overlap > 0

            # Funk-SVD vs Item-KNN score variations
            if model == "funk_svd":
                base_score = 4.3 if is_match else 2.8
                score = base_score + (genre_overlap * 0.15) + ((m["movie_id"] % 10) * 0.02)
            elif model == "item_knn":
                base_score = 4.1 if is_match else 2.9
                # Item-KNN uses neighbor similarity with slightly different ranking weights
                score = base_score + (genre_overlap * 0.12) + (((m["movie_id"] + 3) % 10) * 0.03)
            else:
                score = 3.5 + ((m["movie_id"] % 5) * 0.1)

            score = min(5.0, round(score, 4))
            match_pct = round((score / 5.0) * 100)

            scored_items.append(
                {
                    "movie_id": m["movie_id"],
                    "title": m["title"],
                    "year": m["year"],
                    "genres": m["genres"],
                    "score": score,
                    "match_percentage": match_pct,
                    "poster_path": m["poster_path"],
                    "backdrop_path": m["backdrop_path"],
                }
            )

        scored_items.sort(key=lambda x: x["score"], reverse=True)
        items = scored_items[:limit]

        return {
            "profile_id": profile_id,
            "model": model,
            "total_candidates": len(scored_items),
            "items": items,
        }

    @app.get("/api/v1/recommendations/billboard")
    @app.get("/api/recommendations/billboard")
    def get_billboard(profile_id: str | None = Query("neel")) -> dict[str, Any]:
        if profile_id == "nitin":
            # Drama hero
            hero_candidates = [m for m in CATALOG if "Drama" in m["genres"]]
            hero = hero_candidates[0] if hero_candidates else CATALOG[0]
            match_pct = 97
        elif profile_id == "mukesh":
            # Cold-start popular baseline
            hero = CATALOG[0]
            match_pct = 85
        else:
            # Neel: Action/Sci-Fi hero
            hero_candidates = [
                m for m in CATALOG if "Action" in m["genres"] or "Sci-Fi" in m["genres"]
            ]
            hero = hero_candidates[0] if hero_candidates else CATALOG[0]
            match_pct = 98

        return {
            "movie_id": hero["movie_id"],
            "title": hero["title"],
            "synopsis": hero["synopsis"],
            "backdrop_path": hero["backdrop_path"],
            "poster_path": hero["poster_path"],
            "match_percentage": match_pct,
            "genres": hero["genres"],
            "year": hero["year"],
        }

    @app.get("/api/v1/recommendations/because-you-liked")
    @app.get("/api/recommendations/because-you-liked")
    def get_because_you_liked(profile_id: str = Query(...)) -> dict[str, Any]:
        if profile_id not in state_profiles:
            raise HTTPException(status_code=404, detail="Profile not found")

        p = state_profiles[profile_id]
        ratings = p["ratings"]
        if not ratings:
            seed = CATALOG[0]
        else:
            top_mid = max(ratings.keys(), key=lambda k: ratings[k])
            seed = MOVIE_LOOKUP.get(top_mid, CATALOG[0])

        # Neighbors sharing seed's genres
        seed_genres = set(seed["genres"])
        neighbors = [
            {
                "movie_id": m["movie_id"],
                "title": m["title"],
                "genres": m["genres"],
                "similarity": 0.88 - (idx * 0.03),
                "poster_path": m["poster_path"],
            }
            for idx, m in enumerate(CATALOG)
            if m["movie_id"] != seed["movie_id"] and seed_genres.intersection(m["genres"])
        ][:10]

        return {
            "profile_id": profile_id,
            "seed_movie": {
                "movie_id": seed["movie_id"],
                "title": seed["title"],
                "genres": seed["genres"],
            },
            "recommendations": neighbors,
        }

    @app.get("/api/v1/recommendations/also-watched/{movie_id}")
    @app.get("/api/recommendations/also-watched/{movie_id}")
    def get_also_watched(movie_id: int) -> dict[str, Any]:
        if movie_id not in MOVIE_LOOKUP:
            raise HTTPException(status_code=404, detail="Source movie not found")

        source = MOVIE_LOOKUP[movie_id]
        source_genres = set(source["genres"])

        recommendations = [
            {
                "movie_id": m["movie_id"],
                "title": m["title"],
                "genres": m["genres"],
                "lift": round(max(1.10, 2.80 - (idx * 0.12)), 2),
                "cooccurrence": max(20, 140 - (idx * 6)),
                "match_percentage": max(50, 92 - (idx * 2)),
            }
            for idx, m in enumerate(CATALOG)
            if m["movie_id"] != movie_id and source_genres.intersection(m["genres"])
        ][:10]

        return {
            "source_movie_id": movie_id,
            "recommendations": recommendations,
        }

    @app.post("/api/v1/profiles/{profile_id}/ratings")
    @app.post("/api/profiles/{profile_id}/ratings")
    def submit_rating(profile_id: str, payload: RatingSubmission) -> dict[str, Any]:
        if profile_id not in state_profiles:
            raise HTTPException(status_code=404, detail="Profile not found")
        if payload.movie_id not in MOVIE_LOOKUP:
            raise HTTPException(status_code=404, detail="Movie not found")

        t0 = time.perf_counter()
        p = state_profiles[profile_id]

        is_new = payload.movie_id not in p["ratings"]
        p["ratings"][payload.movie_id] = payload.rating
        if is_new:
            p["ratings_count"] = p.get("ratings_count", 0) + 1
        count = p["ratings_count"]

        unlocked = False
        if profile_id == "mukesh" and count >= 6:
            p["is_cold_start"] = False
            unlocked = True

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "status": "ok",
            "profile_id": profile_id,
            "movie_id": payload.movie_id,
            "rating": payload.rating,
            "ratings_count": count,
            "unlocked": unlocked or not p["is_cold_start"],
            "fold_in_time_ms": round(elapsed_ms, 2),
        }

    @app.get("/api/v1/model-lab/leaderboard")
    @app.get("/api/model-lab/leaderboard")
    def get_leaderboard() -> dict[str, Any]:
        return {
            "models": [
                {
                    "model_id": "popularity",
                    "name": "Bayesian Popularity Baseline",
                    "ndcg_10": 0.0512,
                    "rmse": 1.0210,
                    "mae": 0.8120,
                    "precision_10": 0.0420,
                    "recall_10": 0.0380,
                    "coverage_10": 0.1240,
                },
                {
                    "model_id": "item_knn",
                    "name": "Item-KNN (Adjusted Cosine)",
                    "ndcg_10": 0.0894,
                    "rmse": 0.9080,
                    "mae": 0.7180,
                    "precision_10": 0.0780,
                    "recall_10": 0.0710,
                    "coverage_10": 0.4850,
                },
                {
                    "model_id": "funk_svd",
                    "name": "Funk-SVD (Biased SGD)",
                    "ndcg_10": 0.1042,
                    "rmse": 0.8650,
                    "mae": 0.6790,
                    "precision_10": 0.0910,
                    "recall_10": 0.0840,
                    "coverage_10": 0.6520,
                },
            ]
        }

    @app.get("/api/v1/model-lab/convergence")
    @app.get("/api/model-lab/convergence")
    def get_convergence() -> list[dict[str, Any]]:
        # 20 epochs demonstrating downward loss & RMSE convergence
        epochs = []
        base_loss = 0.95
        base_rmse = 0.99
        for ep in range(1, 21):
            loss = base_loss * (0.97**ep) + 0.05
            rmse = base_rmse * (0.985**ep) + 0.08
            epochs.append(
                {
                    "epoch": ep,
                    "train_loss": round(loss, 4),
                    "val_rmse": round(rmse, 4),
                }
            )
        return epochs

    @app.get("/api/v1/model-lab/compare")
    @app.get("/api/model-lab/compare")
    def compare_models(profile_id: str = Query("neel")) -> dict[str, Any]:
        rec_svd = get_recommendations(profile_id=profile_id, model="funk_svd", limit=10)
        rec_knn = get_recommendations(profile_id=profile_id, model="item_knn", limit=10)
        return {
            "profile_id": profile_id,
            "funk_svd": rec_svd["items"],
            "item_knn": rec_knn["items"],
        }

    @app.get("/api/v1/model-lab/explain")
    @app.get("/api/model-lab/explain")
    def explain_prediction(
        profile_id: str = Query(...),
        movie_id: int = Query(...),
        model: str = Query("funk_svd", pattern="^(funk_svd|item_knn)$"),
    ) -> dict[str, Any]:
        if movie_id not in MOVIE_LOOKUP:
            raise HTTPException(status_code=404, detail="Movie not found")

        movie = MOVIE_LOOKUP[movie_id]

        if model == "funk_svd":
            mu = 3.58
            user_bias = 0.42 if profile_id == "neel" else 0.35
            item_bias = 0.55 if "Action" in movie["genres"] or "Drama" in movie["genres"] else 0.10
            dot_product = 0.25
            predicted = round(mu + user_bias + item_bias + dot_product, 2)
            predicted = min(5.0, max(1.0, predicted))
            return {
                "model": "funk_svd",
                "movie_id": movie_id,
                "title": movie["title"],
                "global_mean": mu,
                "user_bias": user_bias,
                "item_bias": item_bias,
                "latent_dot_product": dot_product,
                "latent_factors_count": 32,
                "predicted_score": predicted,
                "match_percentage": round((predicted / 5.0) * 100),
            }
        else:
            user_mean = 3.90
            predicted = 4.45
            neighbors = [
                {
                    "movie_id": 589,
                    "title": "Terminator 2",
                    "similarity": 0.78,
                    "rating": 5.0,
                    "contribution": 0.42,
                },
                {
                    "movie_id": 260,
                    "title": "Star Wars IV",
                    "similarity": 0.71,
                    "rating": 4.5,
                    "contribution": 0.31,
                },
            ]
            return {
                "model": "item_knn",
                "movie_id": movie_id,
                "title": movie["title"],
                "user_mean": user_mean,
                "neighbors": neighbors,
                "predicted_score": predicted,
                "match_percentage": round((predicted / 5.0) * 100),
            }

    return app
