"""High-fidelity contract-compliant mock application for CineMatch E2E testing.

Implements all endpoints and interface contracts specified in PROJECT.md:
- Tier 1: Single-User Auth (/api/v1/auth/signup, /signin, /me)
- Tier 2: Real TMDB media URLs & Trailers (/api/v1/movies/{id}/trailer, /tmdb/movie/{id}/trailer)
- Tier 3: 6-movie cold-start gating & online fold-in (/api/v1/recommendations, /api/v1/ratings)
- Tier 4: Authenticated user watchlist (/api/v1/watchlist, /watchlist/{id})
- Pre-seeded profiles and model lab contracts for backwards-compatible test coverage
"""

from __future__ import annotations

import copy
import hashlib
import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

# Load real MovieLens catalog if available
ROOT_DIR = Path(__file__).resolve().parents[3]
PARQUET_PATH = ROOT_DIR / "data" / "processed" / "movies.parquet"

CATALOG: list[dict[str, Any]] = []

TMDB_ID_MAP: dict[int, int] = {
    1: 862,
    2571: 603,
    589: 280,
    260: 11,
    318: 278,
    527: 424,
    1196: 1891,
    1721: 597,
    912: 289,
    356: 13,
    550: 550,
}

TRAILER_MAP: dict[int, str] = {
    1: "v-PjgYDrg70",
    2571: "vKQi3bBA1y8",
    589: "CRRlbK5w8AE",
    260: "vZ734NWnAHA",
    318: "PLl99DlL6b4",
    527: "mxphAlJID9U",
    1196: "JNwNXF9Y6kY",
    1721: "kVrqfYjkTdQ",
    912: "MF7JH_54d8c",
    356: "bLvqoHBptjg",
    550: "dfeUzm6KF4g",
}

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
            mid = int(row["movie_id"])
            tmdb_id = TMDB_ID_MAP.get(mid, mid)
            CATALOG.append(
                {
                    "movie_id": mid,
                    "id": mid,
                    "tmdb_id": tmdb_id,
                    "item_idx": int(row["item_idx"])
                    if pd.notna(row.get("item_idx"))
                    else mid,
                    "title": str(row["title"]),
                    "year": year,
                    "genres": genres,
                    "synopsis": f"A compelling film exploring {', '.join(genres) if genres else 'dramatic'} themes.",
                    "director": "Acclaimed Director",
                    "cast": ["Lead Actor", "Supporting Star"],
                    "poster_path": f"https://image.tmdb.org/t/p/w500/{mid}.jpg",
                    "backdrop_path": f"https://image.tmdb.org/t/p/w1280/{mid}.jpg",
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
            "id": 1,
            "tmdb_id": 862,
            "item_idx": 0,
            "title": "Toy Story",
            "year": 1995,
            "genres": ["Animation", "Children's", "Comedy"],
            "synopsis": "A cowboy doll is profoundly threatened...",
            "director": "John Lasseter",
            "cast": ["Tom Hanks", "Tim Allen"],
            "poster_path": "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
            "backdrop_path": "https://image.tmdb.org/t/p/w1280/lxD5ak7BOx0EG9cyIOqEQAhioMf.jpg",
            "vote_average": 4.1,
            "vote_count": 2077,
            "runtime": 81,
        },
        {
            "movie_id": 2571,
            "id": 2571,
            "tmdb_id": 603,
            "item_idx": 1,
            "title": "The Matrix",
            "year": 1999,
            "genres": ["Action", "Sci-Fi"],
            "synopsis": "A computer hacker learns about reality...",
            "director": "Lana Wachowski",
            "cast": ["Keanu Reeves", "Laurence Fishburne"],
            "poster_path": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
            "backdrop_path": "https://image.tmdb.org/t/p/w1280/l4QHerTSbMI7qgRAC427Ej4MtL2.jpg",
            "vote_average": 4.3,
            "vote_count": 2590,
            "runtime": 136,
        },
        {
            "movie_id": 589,
            "id": 589,
            "tmdb_id": 280,
            "item_idx": 2,
            "title": "Terminator 2: Judgment Day",
            "year": 1991,
            "genres": ["Action", "Sci-Fi", "Thriller"],
            "synopsis": "A cyborg is sent back in time...",
            "director": "James Cameron",
            "cast": ["Arnold Schwarzenegger", "Linda Hamilton"],
            "poster_path": "https://image.tmdb.org/t/p/w500/5M0j0B18abtBI5giGR9fhu3TkDx.jpg",
            "backdrop_path": "https://image.tmdb.org/t/p/w1280/xKb6MTnflZnvCgG21T9vWnB9cM0.jpg",
            "vote_average": 4.2,
            "vote_count": 2649,
            "runtime": 137,
        },
        {
            "movie_id": 260,
            "id": 260,
            "tmdb_id": 11,
            "item_idx": 3,
            "title": "Star Wars: Episode IV - A New Hope",
            "year": 1977,
            "genres": ["Action", "Adventure", "Sci-Fi"],
            "synopsis": "Luke Skywalker joins forces with a Jedi Knight...",
            "director": "George Lucas",
            "cast": ["Mark Hamill", "Harrison Ford"],
            "poster_path": "https://image.tmdb.org/t/p/w500/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg",
            "backdrop_path": "https://image.tmdb.org/t/p/w1280/zqkmTXzjkAgPnEgOTs3zSnCVQm5.jpg",
            "vote_average": 4.4,
            "vote_count": 2991,
            "runtime": 121,
        },
        {
            "movie_id": 318,
            "id": 318,
            "tmdb_id": 278,
            "item_idx": 4,
            "title": "The Shawshank Redemption",
            "year": 1994,
            "genres": ["Drama"],
            "synopsis": "Two imprisoned men bond over a number of years...",
            "director": "Frank Darabont",
            "cast": ["Tim Robbins", "Morgan Freeman"],
            "poster_path": "https://image.tmdb.org/t/p/w500/9cqNtx0Gag88v4neofb1s8t9yL.jpg",
            "backdrop_path": "https://image.tmdb.org/t/p/w1280/kXfqcdQKsToO0OUXHcrrNCHDBzO.jpg",
            "vote_average": 4.5,
            "vote_count": 2227,
            "runtime": 142,
        },
        {
            "movie_id": 527,
            "id": 527,
            "tmdb_id": 424,
            "item_idx": 5,
            "title": "Schindler's List",
            "year": 1993,
            "genres": ["Drama", "War"],
            "synopsis": "In German-occupied Poland during World War II...",
            "director": "Steven Spielberg",
            "cast": ["Liam Neeson", "Ben Kingsley"],
            "poster_path": "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg",
            "backdrop_path": "https://image.tmdb.org/t/p/w1280/zb6fM1CX41D9r69hdYvrb0TD0q.jpg",
            "vote_average": 4.5,
            "vote_count": 2304,
            "runtime": 195,
        },
        {
            "movie_id": 1196,
            "id": 1196,
            "tmdb_id": 1891,
            "item_idx": 6,
            "title": "Star Wars: Episode V - The Empire Strikes Back",
            "year": 1980,
            "genres": ["Action", "Adventure", "Sci-Fi"],
            "synopsis": "After the Rebels are brutally overpowered by the Empire...",
            "director": "Irvin Kershner",
            "cast": ["Mark Hamill", "Harrison Ford"],
            "poster_path": "https://image.tmdb.org/t/p/w500/nNAeTmF4A9GQ2grNiWpERAcjxmt.jpg",
            "backdrop_path": "https://image.tmdb.org/t/p/w1280/aJCtkxLLRJJ1Lumn2EZSZtl7r8P.jpg",
            "vote_average": 4.3,
            "vote_count": 2990,
            "runtime": 124,
        },
        {
            "movie_id": 1721,
            "id": 1721,
            "tmdb_id": 597,
            "item_idx": 7,
            "title": "Titanic",
            "year": 1997,
            "genres": ["Drama", "Romance"],
            "synopsis": "A seventeen-year-old aristocrat falls in love with a kind but poor artist...",
            "director": "James Cameron",
            "cast": ["Leonardo DiCaprio", "Kate Winslet"],
            "poster_path": "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg",
            "backdrop_path": "https://image.tmdb.org/t/p/w1280/3W4oM4rU91C7WvM4gXU1wzU0y3I.jpg",
            "vote_average": 4.0,
            "vote_count": 1546,
            "runtime": 194,
        },
        {
            "movie_id": 912,
            "id": 912,
            "tmdb_id": 289,
            "item_idx": 8,
            "title": "Casablanca",
            "year": 1942,
            "genres": ["Drama", "Romance", "War"],
            "synopsis": "A cynical expatriate American cafe owner struggles...",
            "director": "Michael Curtiz",
            "cast": ["Humphrey Bogart", "Ingrid Bergman"],
            "poster_path": "https://image.tmdb.org/t/p/w500/5K7cOHoay2mZusSLezBOY0Qxh8a.jpg",
            "backdrop_path": "https://image.tmdb.org/t/p/w1280/hZkgoQYus5vegHoetLkCJzb17zJ.jpg",
            "vote_average": 4.4,
            "vote_count": 1669,
            "runtime": 102,
        },
        {
            "movie_id": 356,
            "id": 356,
            "tmdb_id": 13,
            "item_idx": 9,
            "title": "Forrest Gump",
            "year": 1994,
            "genres": ["Comedy", "Drama", "Romance"],
            "synopsis": "The history of the United States from the 1950s to the '70s...",
            "director": "Robert Zemeckis",
            "cast": ["Tom Hanks", "Robin Wright"],
            "poster_path": "https://image.tmdb.org/t/p/w500/arw2VCBveWOVZr6pxd9XTd1TdQa.jpg",
            "backdrop_path": "https://image.tmdb.org/t/p/w1280/qdIMhmSlMAZYCdUMzn9HGtmp0W5.jpg",
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


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class SigninRequest(BaseModel):
    email: str
    password: str


class AuthRatingSubmission(BaseModel):
    movie_id: int
    rating: float


class WatchlistCreatePayload(BaseModel):
    movie_id: int | None = None
    id: int | None = None
    list_type: str = "watchlist"


def create_contract_app() -> FastAPI:
    """Create FastAPI application fulfilling CineMatch E2E contracts."""
    app = FastAPI(title="CineMatch E2E Contract Service", version="1.0.0")

    # Mutable state for tests
    state_profiles: dict[str, dict[str, Any]] = copy.deepcopy(INITIAL_PROFILES)
    state_users: dict[str, dict[str, Any]] = {}
    state_tokens: dict[str, dict[str, Any]] = {}
    state_user_ratings: dict[str, dict[int, float]] = {}
    state_user_watchlists: dict[str, list[dict[str, Any]]] = {}

    def _authenticate_user(authorization: str | None) -> dict[str, Any]:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        token = authorization[7:].strip()
        if token not in state_tokens:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return state_tokens[token]

    @app.post("/api/v1/profiles/reset")
    @app.post("/api/profiles/reset")
    @app.post("/api/v1/auth/reset")
    @app.post("/api/auth/reset")
    def reset_profiles() -> dict[str, str]:
        nonlocal state_profiles, state_users, state_tokens, state_user_ratings, state_user_watchlists
        state_profiles = copy.deepcopy(INITIAL_PROFILES)
        state_users.clear()
        state_tokens.clear()
        state_user_ratings.clear()
        state_user_watchlists.clear()
        return {"status": "reset_successful"}

    # ==========================================
    # Tier 1: Single-User Authentication Endpoints
    # ==========================================
    @app.post("/api/v1/auth/signup", status_code=status.HTTP_201_CREATED)
    @app.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
    def signup(payload: SignupRequest) -> dict[str, Any]:
        raw_email = payload.email.strip()
        norm_email = raw_email.lower()
        if not norm_email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", norm_email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")
        if len(payload.password.strip()) < 6:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters")
        if norm_email in state_users:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

        user_id = f"usr_{hashlib.sha256(norm_email.encode()).hexdigest()[:10]}"
        token = f"jwt_{user_id}_{int(time.time() * 1000)}"
        user_data = {
            "id": user_id,
            "email": norm_email,
            "name": (payload.name or norm_email.split("@")[0]).strip(),
            "avatar": "https://lh3.googleusercontent.com/aida-public/AB6AXuCSd426GvWbH5o01V_P1s_mYVf75hA3u8hZndH9n10Y4x=s96-c",
            "ratings_count": 0,
            "is_cold_start": True,
            "taste_vector": None,
        }
        state_users[norm_email] = {
            "user": user_data,
            "password": payload.password,
            "token": token,
        }
        state_tokens[token] = user_data
        state_user_ratings[user_id] = {}
        state_user_watchlists[user_id] = []
        return {"token": token, "user": user_data}

    @app.post("/api/v1/auth/signin", status_code=status.HTTP_200_OK)
    @app.post("/api/auth/signin", status_code=status.HTTP_200_OK)
    def signin(payload: SigninRequest) -> dict[str, Any]:
        norm_email = payload.email.strip().lower()
        if not norm_email or not payload.password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password required")
        if norm_email not in state_users or state_users[norm_email]["password"] != payload.password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        rec = state_users[norm_email]
        return {"token": rec["token"], "user": rec["user"]}

    @app.get("/api/v1/auth/me", status_code=status.HTTP_200_OK)
    @app.get("/api/auth/me", status_code=status.HTTP_200_OK)
    def auth_me(authorization: str | None = Header(None)) -> dict[str, Any]:
        return _authenticate_user(authorization)

    # ==========================================
    # Tier 2: Real TMDB Trailer Extraction
    # ==========================================
    @app.get("/api/v1/movies/{movie_id}/trailer")
    @app.get("/api/movies/{movie_id}/trailer")
    def get_movie_trailer(movie_id: int) -> dict[str, Any]:
        if movie_id not in MOVIE_LOOKUP:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Movie with ID {movie_id} not found")
        movie = MOVIE_LOOKUP[movie_id]
        key = TRAILER_MAP.get(movie_id, f"trailer_{movie_id}")
        return {
            "movie_id": movie_id,
            "tmdb_id": movie.get("tmdb_id", movie_id),
            "title": movie["title"],
            "key": key,
            "site": "YouTube",
            "embed_url": f"https://www.youtube.com/embed/{key}?autoplay=1",
            "watch_url": f"https://www.youtube.com/watch?v={key}",
        }

    @app.get("/api/v1/tmdb/movie/{tmdb_id}/trailer")
    @app.get("/api/tmdb/movie/{tmdb_id}/trailer")
    def get_tmdb_trailer(tmdb_id: int) -> dict[str, Any]:
        m = next((item for item in CATALOG if item.get("tmdb_id") == tmdb_id), None)
        movie_id = m["movie_id"] if m else tmdb_id
        title = m["title"] if m else f"TMDB Title {tmdb_id}"
        key = TRAILER_MAP.get(movie_id, f"tmdb_trailer_{tmdb_id}")
        return {
            "movie_id": movie_id,
            "tmdb_id": tmdb_id,
            "title": title,
            "key": key,
            "site": "YouTube",
            "embed_url": f"https://www.youtube.com/embed/{key}?autoplay=1",
            "watch_url": f"https://www.youtube.com/watch?v={key}",
        }

    # ==========================================
    # Tier 3: 6-Movie Cold-Start Gating & Fold-In
    # ==========================================
    @app.get("/api/v1/recommendations")
    @app.get("/api/recommendations")
    def get_authenticated_recommendations(
        authorization: str | None = Header(None),
        model: str = Query("funk_svd"),
        limit: int = Query(20, ge=1, le=100),
    ) -> dict[str, Any]:
        user = _authenticate_user(authorization)
        ratings = state_user_ratings.get(user["id"], {})
        count = len(ratings)
        if count < 6:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cold start profile requires at least 6 ratings. Currently rated: {count}/6.",
            )
        items = [
            {
                "movie_id": m["movie_id"],
                "title": m["title"],
                "year": m["year"],
                "genres": m["genres"],
                "score": 4.5,
                "match_percentage": 92,
                "poster_path": m["poster_path"],
                "backdrop_path": m["backdrop_path"],
            }
            for m in CATALOG if m["movie_id"] not in ratings
        ][:limit]
        return {
            "user_id": user["id"],
            "model": model,
            "total_candidates": len(items),
            "items": items,
        }

    @app.post("/api/v1/ratings")
    @app.post("/api/ratings")
    def submit_authenticated_rating(
        payload: AuthRatingSubmission,
        authorization: str | None = Header(None),
    ) -> dict[str, Any]:
        user = _authenticate_user(authorization)
        if payload.movie_id not in MOVIE_LOOKUP:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Movie {payload.movie_id} not found")
        if payload.rating < 0.5 or payload.rating > 5.0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rating must be between 0.5 and 5.0")

        t0 = time.perf_counter()
        ratings = state_user_ratings.setdefault(user["id"], {})
        ratings[payload.movie_id] = payload.rating
        count = len(ratings)
        unlocked = count >= 6
        user["ratings_count"] = count
        user["is_cold_start"] = not unlocked
        if unlocked:
            user["taste_vector"] = [0.1] * 32
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "status": "ok",
            "ratings_count": count,
            "unlocked": unlocked,
            "fold_in_time_ms": round(elapsed_ms, 2),
            "message": "Recommendations unlocked!" if unlocked else "Rating recorded",
        }

    # ==========================================
    # Tier 4: Watchlist Endpoints for Authenticated User
    # ==========================================
    @app.get("/api/v1/watchlist")
    @app.get("/api/watchlist")
    def get_watchlist(
        authorization: str | None = Header(None),
        profile_id: str | None = Query(None),
        x_profile_id: str | None = Header(None, alias="x-profile-id"),
    ) -> list[dict[str, Any]]:
        if authorization and authorization.startswith("Bearer "):
            tok = authorization[7:].strip()
            if tok in state_tokens:
                user = state_tokens[tok]
                return state_user_watchlists.get(user["id"], [])
        pid = profile_id or x_profile_id
        if pid:
            if pid not in state_profiles:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Profile '{pid}' not found")
            return state_user_watchlists.get(pid, [])
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    @app.post("/api/v1/watchlist/{movie_id}", status_code=status.HTTP_201_CREATED)
    @app.post("/api/watchlist/{movie_id}", status_code=status.HTTP_201_CREATED)
    def add_watchlist_by_id(
        movie_id: int,
        authorization: str | None = Header(None),
        profile_id: str | None = Query(None),
        x_profile_id: str | None = Header(None, alias="x-profile-id"),
    ) -> dict[str, Any]:
        target_id = None
        if authorization and authorization.startswith("Bearer "):
            tok = authorization[7:].strip()
            if tok in state_tokens:
                target_id = state_tokens[tok]["id"]
        if not target_id:
            target_id = profile_id or x_profile_id
        if not target_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        if movie_id not in MOVIE_LOOKUP:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Movie {movie_id} not found")

        m = MOVIE_LOOKUP[movie_id]
        wl = state_user_watchlists.setdefault(target_id, [])
        if not any(item["movie_id"] == movie_id or item["id"] == movie_id for item in wl):
            wl.append({
                "id": movie_id,
                "movie_id": movie_id,
                "title": m["title"],
                "poster_path": m["poster_path"],
                "backdrop_path": m["backdrop_path"],
                "release_year": m["year"],
                "year": m["year"],
                "genres": m["genres"],
                "vote_average": m["vote_average"],
                "vote_count": m["vote_count"],
                "added_at": "2026-10-10T12:00:00Z",
                "synopsis": m["synopsis"],
                "list_type": "watchlist",
            })
        return {"status": "added", "movie_id": movie_id, "user_id": target_id}

    @app.post("/api/v1/watchlist", status_code=status.HTTP_201_CREATED)
    @app.post("/api/watchlist", status_code=status.HTTP_201_CREATED)
    def add_watchlist_body(
        payload: WatchlistCreatePayload,
        authorization: str | None = Header(None),
        profile_id: str | None = Query(None),
        x_profile_id: str | None = Header(None, alias="x-profile-id"),
    ) -> dict[str, Any]:
        mid = payload.movie_id or payload.id
        if mid is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="movie_id or id is required")
        return add_watchlist_by_id(
            movie_id=mid,
            authorization=authorization,
            profile_id=profile_id,
            x_profile_id=x_profile_id,
        )

    @app.delete("/api/v1/watchlist/{movie_id}", status_code=status.HTTP_200_OK)
    @app.delete("/api/watchlist/{movie_id}", status_code=status.HTTP_200_OK)
    def remove_watchlist_by_id(
        movie_id: int,
        authorization: str | None = Header(None),
        profile_id: str | None = Query(None),
        x_profile_id: str | None = Header(None, alias="x-profile-id"),
    ) -> dict[str, Any]:
        target_id = None
        if authorization and authorization.startswith("Bearer "):
            tok = authorization[7:].strip()
            if tok in state_tokens:
                target_id = state_tokens[tok]["id"]
        if not target_id:
            target_id = profile_id or x_profile_id
        if not target_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        wl = state_user_watchlists.setdefault(target_id, [])
        state_user_watchlists[target_id] = [
            item for item in wl if item["movie_id"] != movie_id and item["id"] != movie_id
        ]
        return {"status": "removed", "movie_id": movie_id, "user_id": target_id}

    # ==========================================
    # Legacy Profile Endpoints for Backward Compatibility
    # ==========================================
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

    @app.get("/api/v1/profiles/{profile_id}/watchlist")
    @app.get("/api/profiles/{profile_id}/watchlist")
    def get_profile_watchlist(profile_id: str) -> list[dict[str, Any]]:
        if profile_id not in state_profiles:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
        wl = state_user_watchlists.setdefault(profile_id, [])
        if not wl and profile_id == "neel":
            # Baseline seeded item for Neel
            m = CATALOG[0]
            wl.append({
                "id": m["movie_id"],
                "movie_id": m["movie_id"],
                "title": m["title"],
                "poster_path": m["poster_path"],
                "release_year": m["year"],
                "genres": m["genres"],
                "added_at": "2026-10-10T10:00:00Z",
            })
        return wl

    @app.post("/api/v1/profiles/{profile_id}/watchlist/{movie_id}", status_code=status.HTTP_201_CREATED)
    @app.post("/api/profiles/{profile_id}/watchlist/{movie_id}", status_code=status.HTTP_201_CREATED)
    def add_profile_watchlist(profile_id: str, movie_id: int) -> dict[str, Any]:
        return add_watchlist_by_id(movie_id=movie_id, profile_id=profile_id)

    @app.delete("/api/v1/profiles/{profile_id}/watchlist/{movie_id}", status_code=status.HTTP_200_OK)
    @app.delete("/api/profiles/{profile_id}/watchlist/{movie_id}", status_code=status.HTTP_200_OK)
    def remove_profile_watchlist(profile_id: str, movie_id: int) -> dict[str, Any]:
        return remove_watchlist_by_id(movie_id=movie_id, profile_id=profile_id)

    @app.get("/api/v1/movies/starter")
    @app.get("/api/movies/starter")
    def get_starter_movies() -> list[dict[str, Any]]:
        return CATALOG[:24]

    @app.get("/api/v1/movies")
    @app.get("/api/movies")
    def list_movies_catalog(
        genre: str | None = Query(None),
        search: str | None = Query(None),
        sort: str | None = Query("top_rated"),
        limit: int = Query(24, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ) -> dict[str, Any]:
        results = CATALOG
        if genre:
            gl = genre.lower()
            results = [m for m in results if any(g.lower() == gl for g in m["genres"])]
        if search:
            s_clean = search.strip().lower()
            results = [m for m in results if s_clean in m["title"].lower()]
        total = len(results)
        items = results[offset : offset + limit]
        return {"items": items, "total": total, "genre": genre}

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

        if profile_id == "mukesh" and current_count < 6:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cold start profile requires at least 6 ratings. Currently rated: {current_count}/6.",
            )

        scored_items: list[dict[str, Any]] = []

        if profile_id == "neel":
            preferred_genres = {"Action", "Sci-Fi", "Adventure", "Thriller"}
        elif profile_id == "nitin":
            preferred_genres = {"Drama", "Romance", "War"}
        else:
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
            if m["movie_id"] in current_ratings:
                continue

            genre_overlap = len(set(m["genres"]).intersection(preferred_genres))
            is_match = genre_overlap > 0

            if model == "funk_svd":
                base_score = 4.3 if is_match else 2.8
                score = base_score + (genre_overlap * 0.15) + ((m["movie_id"] % 10) * 0.02)
            elif model == "item_knn":
                base_score = 4.1 if is_match else 2.9
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
            hero_candidates = [m for m in CATALOG if "Drama" in m["genres"]]
            hero = hero_candidates[0] if hero_candidates else CATALOG[0]
            match_pct = 97
        elif profile_id == "mukesh":
            hero = CATALOG[0]
            match_pct = 85
        else:
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
