"""Data preparation: parsing .dat files, cleaning titles, indexing, parquet export."""
import json
import re
from pathlib import Path
from typing import Tuple, Optional
import pandas as pd
from recsys.config import RAW_DIR, PROCESSED_DIR, ARTIFACTS_DIR

TITLE_REGEX = re.compile(r"^(?P<title>.*) \((?P<year>\d{4})\)$")
ARTICLE_REGEX = re.compile(
    r"^(?P<base>.*), (?P<art>The|A|An|La|Le|Les|Il|El|Das|Der|Die)$",
    re.IGNORECASE,
)


def clean_title_and_year(raw_title: str) -> Tuple[str, Optional[int]]:
    """Clean MovieLens movie title and extract year.
    
    Examples:
        'Matrix, The (1999)' -> ('The Matrix', 1999)
        'Star Wars: Episode IV - A New Hope (1977)' -> ('Star Wars: Episode IV - A New Hope', 1977)
    """
    raw_title = raw_title.strip()
    match = TITLE_REGEX.match(raw_title)
    if match:
        base_title = match.group("title").strip()
        year = int(match.group("year"))
    else:
        base_title = raw_title
        year = None

    art_match = ARTICLE_REGEX.match(base_title)
    if art_match:
        base = art_match.group("base").strip()
        art = art_match.group("art").strip()
        cleaned_title = f"{art} {base}"
    else:
        cleaned_title = base_title

    return cleaned_title, year


def prepare_dataset(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    artifacts_dir: Path = ARTIFACTS_DIR,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Parse MovieLens 1M dat files, normalize titles, create contiguous IDs, save Parquet & JSON."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    print("[recsys] Parsing ratings.dat...")
    ratings = pd.read_csv(
        raw_dir / "ratings.dat",
        sep="::",
        engine="python",
        names=["user_id", "movie_id", "rating", "timestamp"],
        dtype={"user_id": "int32", "movie_id": "int32", "rating": "int8", "timestamp": "int64"},
    )
    ratings["ts"] = pd.to_datetime(ratings["timestamp"], unit="s")

    print("[recsys] Parsing movies.dat...")
    movies = pd.read_csv(
        raw_dir / "movies.dat",
        sep="::",
        engine="python",
        names=["movie_id", "title_raw", "genres_raw"],
        encoding="latin-1",
        dtype={"movie_id": "int32"},
    )

    cleaned_titles_and_years = [clean_title_and_year(t) for t in movies["title_raw"]]
    movies["title"] = [t[0] for t in cleaned_titles_and_years]
    movies["year"] = [t[1] for t in cleaned_titles_and_years]
    movies["genres"] = movies["genres_raw"].apply(lambda g: g.split("|") if pd.notna(g) else [])

    print("[recsys] Parsing users.dat...")
    users = pd.read_csv(
        raw_dir / "users.dat",
        sep="::",
        engine="python",
        names=["user_id", "gender", "age", "occupation", "zip_code"],
        encoding="latin-1",
        dtype={"user_id": "int32"},
    )

    # Filter movies with at least 1 rating
    rated_movie_ids = sorted(ratings["movie_id"].unique())
    user_ids = sorted(ratings["user_id"].unique())

    # Build contiguous indices (0 .. N-1)
    movie_id_to_item_idx = {int(mid): int(idx) for idx, mid in enumerate(rated_movie_ids)}
    item_idx_to_movie_id = {int(idx): int(mid) for idx, mid in enumerate(rated_movie_ids)}
    user_id_to_user_idx = {int(uid): int(idx) for idx, uid in enumerate(user_ids)}
    user_idx_to_user_id = {int(idx): int(uid) for idx, uid in enumerate(user_ids)}

    # Map to ratings
    ratings["user_idx"] = ratings["user_id"].map(user_id_to_user_idx).astype("int32")
    ratings["item_idx"] = ratings["movie_id"].map(movie_id_to_item_idx).astype("int32")

    # Map item_idx to movies dataframe (unrated movies have item_idx = None)
    movies["item_idx"] = movies["movie_id"].map(movie_id_to_item_idx).astype("Int32")

    # Save id maps
    id_maps = {
        "n_users": len(user_ids),
        "n_items": len(rated_movie_ids),
        "movie_id_to_item_idx": movie_id_to_item_idx,
        "item_idx_to_movie_id": item_idx_to_movie_id,
        "user_id_to_user_idx": user_id_to_user_idx,
        "user_idx_to_user_id": user_idx_to_user_id,
    }
    with open(processed_dir / "id_maps.json", "w", encoding="utf-8") as f:
        json.dump(id_maps, f)
    with open(artifacts_dir / "id_maps.json", "w", encoding="utf-8") as f:
        json.dump(id_maps, f)

    # Save Parquet
    ratings.to_parquet(processed_dir / "ratings.parquet", index=False)
    movies.to_parquet(processed_dir / "movies.parquet", index=False)
    users.to_parquet(processed_dir / "users.parquet", index=False)

    print(
        f"[recsys] Prepared {len(ratings):,} ratings, {len(user_ids):,} users, "
        f"{len(rated_movie_ids):,} rated movies (out of {len(movies):,} total movies)."
    )
    return ratings, movies, users


if __name__ == "__main__":
    prepare_dataset()
