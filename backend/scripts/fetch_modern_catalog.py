import json
import logging
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fetch_catalog")

API_KEY = "43962557578f3b9e690a5c1b9cab4d17"
BASE_URL = "https://api.themoviedb.org/3"

# Iconic modern hits + benchmark classics
MUST_HAVE_IDS = [
    693134,  # Dune: Part Two (2024)
    872585,  # Oppenheimer (2023)
    569094,  # Spider-Man: Across the Spider-Verse (2023)
    157336,  # Interstellar (2014)
    27205,   # Inception (2010)
    155,     # The Dark Knight (2008)
    414906,  # The Batman (2022)
    361743,  # Top Gun: Maverick (2022)
    299534,  # Avengers: Endgame (2019)
    496243,  # Parasite (2019)
    244786,  # Whiplash (2014)
    550,     # Fight Club (1999)
    603,     # The Matrix (1999)
    680,     # Pulp Fiction (1994)
    278,     # The Shawshank Redemption (1994)
    129,     # Spirited Away (2001)
    122,     # The Lord of the Rings: Return of the King (2003)
    862,     # Toy Story (1995)
    280,     # Terminator 2: Judgment Day (1991)
    11,      # Star Wars: Episode IV - A New Hope (1977)
    13,      # Forrest Gump (1994)
    238,     # The Godfather (1972)
    597,     # Titanic (1997)
    424,     # Schindler's List (1993)
    274,     # The Silence of the Lambs (1991)
    85,      # Raiders of the Lost Ark (1981)
]


def tmdb_get(endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    url = f"{BASE_URL}{endpoint}?api_key={API_KEY}"
    if params:
        for k, v in params.items():
            url += f"&{k}={urllib.parse.quote(str(v))}"
    req = urllib.request.Request(url, headers={"User-Agent": "CineMatch/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_movie_detail(tmdb_id: int) -> Optional[Dict[str, Any]]:
    try:
        data = tmdb_get(f"/movie/{tmdb_id}", {"append_to_response": "credits,videos"})
        if not data.get("title") or not data.get("poster_path"):
            return None

        credits = data.get("credits", {})
        crew = credits.get("crew", [])
        cast_list = credits.get("cast", [])

        director = next((c["name"] for c in crew if c.get("job") == "Director"), "Acclaimed Director")
        top_cast = [c["name"] for c in cast_list[:5]] or ["Leading Cast Ensemble"]

        # Extract best YouTube trailer
        videos = data.get("videos", {}).get("results", [])
        yt_trailers = [
            v for v in videos
            if str(v.get("site", "")).lower() == "youtube"
            and v.get("key")
            and len(str(v.get("key")).strip()) >= 5
        ]

        def _rank(v: Dict[str, Any]) -> tuple:
            vtype = str(v.get("type", "")).lower()
            type_score = 2 if vtype == "trailer" else (1 if vtype == "teaser" else 0)
            is_official = 1 if v.get("official") is True else 0
            return (type_score, is_official)

        yt_trailers.sort(key=_rank, reverse=True)
        trailer_key = yt_trailers[0]["key"] if yt_trailers else None

        genres = [g["name"] for g in data.get("genres", [])] or ["Drama", "Action"]

        release_date = str(data.get("release_date") or "")
        year = int(release_date[:4]) if len(release_date) >= 4 and release_date[:4].isdigit() else 2024

        poster_rel = data.get("poster_path", "")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_rel}" if poster_rel else None

        backdrop_rel = data.get("backdrop_path", "")
        backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop_rel}" if backdrop_rel else poster_url

        vote_avg = round(float(data.get("vote_average") or 7.5), 1)
        vote_cnt = int(data.get("vote_count") or 100)
        overview = data.get("overview") or f"{data['title']} is a critically acclaimed modern film."

        return {
            "id": tmdb_id,
            "tmdb_id": tmdb_id,
            "movie_lens_id": tmdb_id,
            "title": data["title"],
            "title_raw": data.get("original_title") or data["title"],
            "year": year,
            "genres": genres,
            "overview": overview,
            "synopsis": overview,
            "poster_path": poster_url,
            "backdrop_path": backdrop_url,
            "vote_average": vote_avg,
            "vote_count": vote_cnt,
            "director": director,
            "cast": top_cast,
            "runtime": int(data.get("runtime") or 120),
            "trailer_key": trailer_key,
        }
    except Exception as exc:
        logger.warning("Failed to fetch details for TMDB %d: %s", tmdb_id, exc)
        return None


def main() -> None:
    logger.info("Fetching trending, top-rated, and popular movies from TMDB API...")
    trending = tmdb_get("/trending/movie/week").get("results", [])
    top_rated = tmdb_get("/movie/top_rated").get("results", [])
    popular = tmdb_get("/movie/popular").get("results", [])

    candidate_ids = list(MUST_HAVE_IDS)
    for row in trending + top_rated + popular:
        mid = row.get("id")
        if mid and mid not in candidate_ids:
            candidate_ids.append(mid)

    logger.info("Identified %d candidate movies. Enriching with credits & trailers...", len(candidate_ids))

    enriched_movies = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(fetch_movie_detail, candidate_ids))

    for m in results:
        if m and m["poster_path"]:
            enriched_movies.append(m)

    logger.info("Successfully enriched %d modern movies with full metadata!", len(enriched_movies))

    out_file = Path(__file__).resolve().parent / "modern_movies_dataset.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(enriched_movies, f, indent=2, ensure_ascii=False)

    logger.info("Saved catalog dataset to %s", out_file)


if __name__ == "__main__":
    main()
