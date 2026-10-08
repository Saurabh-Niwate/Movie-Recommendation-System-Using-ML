import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

# Add backend directory to sys.path so app modules are discoverable
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, engine, ensure_schema_exists
from app.models import Movie, Profile, Rating, UserList
from app.services.tmdb import (
    generate_svg_poster,
    generate_svg_backdrop,
    generate_deterministic_synopsis,
    generate_deterministic_credits,
    _normalize_genres,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cinematch.seeder")


def _find_data_file(filename: str) -> Path:
    """Locate data file in standard workspace paths."""
    candidates = [
        Path.cwd() / "data" / "processed" / filename,
        backend_dir.parent / "data" / "processed" / filename,
        Path("/home/yoogkadu/Documents/SEM 5/ML project/data/processed") / filename,
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError(f"Could not locate {filename} in {candidates}")


def seed_movies(db: Session, reset: bool = False) -> int:
    """Seed movies catalog from MovieLens processed parquet."""
    movies_path = _find_data_file("movies.parquet")
    logger.info("Reading movies catalog from %s", movies_path)
    df = pd.read_parquet(movies_path)

    existing_count = db.query(Movie).count()
    if existing_count > 0 and not reset:
        logger.info("Found %d existing movies in DB, skipping movie seeding", existing_count)
        return existing_count

    if reset and existing_count > 0:
        logger.info("Reset requested: clearing existing ratings, user_lists, and movies...")
        db.execute(text("TRUNCATE TABLE cinematch.ratings CASCADE;"))
        db.execute(text("TRUNCATE TABLE cinematch.user_lists CASCADE;"))
        db.execute(text("TRUNCATE TABLE cinematch.movies CASCADE;"))
        db.commit()

    logger.info("Preparing metadata enrichment for %d movies...", len(df))
    movie_objects = []

    for _, row in df.iterrows():
        mid = int(row["movie_id"])
        title = str(row["title"])
        title_raw = str(row["title_raw"]) if pd.notna(row.get("title_raw")) else title
        year = int(row["year"]) if pd.notna(row.get("year")) else None
        genres_list = _normalize_genres(row.get("genres"))
        item_idx = int(row["item_idx"]) if pd.notna(row.get("item_idx")) else None

        # Deterministic rich visual & narrative metadata
        poster_uri = generate_svg_poster(title, year=year, genres=genres_list, movie_id=mid)
        backdrop_uri = generate_svg_backdrop(title, year=year, genres=genres_list, movie_id=mid)
        synopsis = generate_deterministic_synopsis(title, year=year, genres=genres_list, movie_id=mid)
        credits_info = generate_deterministic_credits(genres=genres_list, movie_id=mid)

        movie_objects.append(
            Movie(
                id=mid,
                movie_lens_id=mid,
                title=title,
                title_raw=title_raw,
                year=year,
                genres=genres_list,
                synopsis=synopsis,
                overview=synopsis,
                poster_path=poster_uri,
                backdrop_path=backdrop_uri,
                tmdb_id=100000 + mid,
                item_idx=item_idx,
                vote_average=credits_info["vote_average"],
                vote_count=credits_info["vote_count"],
                director=credits_info["director"],
                cast=credits_info["cast"],
                runtime=credits_info["runtime"],
            )
        )

    # Batch insert movies
    batch_size = 500
    for i in range(0, len(movie_objects), batch_size):
        db.add_all(movie_objects[i : i + batch_size])
        db.flush()
    db.commit()

    total_inserted = db.query(Movie).count()
    logger.info("Successfully seeded %d movies into cinematch.movies", total_inserted)
    return total_inserted


def seed_profiles_and_ratings(db: Session, reset: bool = False) -> Dict[str, Any]:
    """Seed demo profiles (Neel, Nitin, Mukesh) and pre-load train ratings."""
    train_path = _find_data_file("train.parquet")
    logger.info("Reading train ratings from %s", train_path)
    train_df = pd.read_parquet(train_path)

    profiles_data = [
        {
            "id": "neel",
            "name": "Neel",
            "avatar": "/avatars/neel.png",
            "bio": "Action & Sci-Fi enthusiast. Loves cyberpunk worlds, space operas, and mind-bending thrillers.",
            "taste_cluster": "Action / Sci-Fi",
            "user_idx": 2955,
            "is_demo": True,
            "is_cold_start": False,
        },
        {
            "id": "nitin",
            "name": "Nitin",
            "avatar": "/avatars/nitin.png",
            "bio": "Drama & Romance enthusiast. Drawn to character-driven storytelling, timeless romance, and emotional journeys.",
            "taste_cluster": "Drama / Romance",
            "user_idx": 2583,
            "is_demo": True,
            "is_cold_start": False,
        },
        {
            "id": "mukesh",
            "name": "Mukesh",
            "avatar": "/avatars/mukesh.png",
            "bio": "New cinephile building my movie profile. Cold-start user discovering new favorites.",
            "taste_cluster": "Cold Start",
            "user_idx": None,
            "is_demo": True,
            "is_cold_start": True,
            "ratings_count": 0,
        },
    ]

    results = {}

    for p_spec in profiles_data:
        pid = p_spec["id"]
        profile = db.query(Profile).filter(Profile.id == pid).first()

        if profile is None:
            profile = Profile(
                id=pid,
                name=p_spec["name"],
                avatar=p_spec["avatar"],
                bio=p_spec["bio"],
                taste_cluster=p_spec["taste_cluster"],
                user_idx=p_spec["user_idx"],
                is_demo=p_spec["is_demo"],
                is_cold_start=p_spec["is_cold_start"],
                ratings_count=0,
            )
            db.add(profile)
            db.flush()
        elif reset:
            profile.name = p_spec["name"]
            profile.avatar = p_spec["avatar"]
            profile.bio = p_spec["bio"]
            profile.taste_cluster = p_spec["taste_cluster"]
            profile.user_idx = p_spec["user_idx"]
            profile.is_demo = p_spec["is_demo"]
            profile.is_cold_start = p_spec["is_cold_start"]
            profile.ratings_count = 0
            # Remove old ratings for reset
            db.query(Rating).filter(Rating.profile_id == pid).delete()
            db.flush()

        # Seed ratings if demo user with user_idx
        u_idx = p_spec["user_idx"]
        seeded_ratings_count = 0

        if u_idx is not None:
            user_ratings = train_df[train_df["user_idx"] == u_idx]
            existing_rating_movie_ids = {
                r.movie_id
                for r in db.query(Rating.movie_id).filter(Rating.profile_id == pid).all()
            }

            ratings_to_add = []
            for _, r_row in user_ratings.iterrows():
                mid = int(r_row["movie_id"])
                if mid in existing_rating_movie_ids:
                    continue
                score = float(r_row["rating"])
                item_idx = int(r_row["item_idx"]) if pd.notna(r_row.get("item_idx")) else None

                ratings_to_add.append(
                    Rating(
                        profile_id=pid,
                        movie_id=mid,
                        rating=score,
                        item_idx=item_idx,
                    )
                )

            if ratings_to_add:
                db.add_all(ratings_to_add)
                db.flush()

            total_ratings = db.query(Rating).filter(Rating.profile_id == pid).count()
            profile.ratings_count = total_ratings
            seeded_ratings_count = total_ratings
        else:
            profile.ratings_count = 0
            profile.is_cold_start = True

        db.commit()
        results[pid] = {
            "name": profile.name,
            "ratings_count": profile.ratings_count,
            "is_cold_start": profile.is_cold_start,
            "user_idx": profile.user_idx,
        }
        logger.info(
            "Profile '%s' ready: ratings_count=%d, is_cold_start=%s",
            pid,
            profile.ratings_count,
            profile.is_cold_start,
        )

    return results


def seed_demo_user_lists(db: Session) -> None:
    """Pre-seed sample watchlists for demo profiles."""
    existing = db.query(UserList).count()
    if existing > 0:
        return

    # Add sample watchlist items for Neel and Nitin
    sample_lists = [
        UserList(profile_id="neel", movie_id=2571, list_type="watchlist"),  # The Matrix
        UserList(profile_id="neel", movie_id=260, list_type="favorites"),   # Star Wars: Ep IV
        UserList(profile_id="nitin", movie_id=1721, list_type="watchlist"), # Titanic
        UserList(profile_id="nitin", movie_id=318, list_type="favorites"),  # Shawshank Redemption
    ]
    # Filter to only movies that exist
    movie_ids = {m[0] for m in db.query(Movie.id).all()}
    valid_items = [item for item in sample_lists if item.movie_id in movie_ids]

    if valid_items:
        db.add_all(valid_items)
        db.commit()
        logger.info("Seeded %d sample user_list items", len(valid_items))


def main() -> None:
    """Execute complete database seeding pipeline."""
    reset = "--reset" in sys.argv
    ensure_schema_exists()

    db = SessionLocal()
    try:
        logger.info("=== Starting CineMatch Database Seeding ===")
        movie_count = seed_movies(db, reset=reset)
        profile_results = seed_profiles_and_ratings(db, reset=reset)
        seed_demo_user_lists(db)

        logger.info("=== Seeding Completed Successfully ===")
        logger.info("Total Movies: %d", movie_count)
        for pid, pdata in profile_results.items():
            logger.info(
                "Profile '%s' (%s): ratings=%d, cold_start=%s",
                pid,
                pdata["name"],
                pdata["ratings_count"],
                pdata["is_cold_start"],
            )
    except Exception as exc:
        db.rollback()
        logger.error("Seeding failed: %s", exc, exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
