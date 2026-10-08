import base64
import hashlib
import html
import logging
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# Genre-to-color palette themes (primary color, secondary color, accent color, text color)
GENRE_PALETTES: Dict[str, Dict[str, str]] = {
    "Action": {"c1": "#1a0404", "c2": "#3b0808", "accent": "#e50914", "badge": "#ff3838"},
    "Adventure": {"c1": "#04141a", "c2": "#092f3b", "accent": "#00b4d8", "badge": "#48cae4"},
    "Animation": {"c1": "#041a15", "c2": "#093b30", "accent": "#10b981", "badge": "#34d399"},
    "Children": {"c1": "#12041a", "c2": "#28093b", "accent": "#ec4899", "badge": "#f472b6"},
    "Children's": {"c1": "#12041a", "c2": "#28093b", "accent": "#ec4899", "badge": "#f472b6"},
    "Comedy": {"c1": "#1a1604", "c2": "#3b3009", "accent": "#f59e0b", "badge": "#fbbf24"},
    "Crime": {"c1": "#0d0d12", "c2": "#1c1b24", "accent": "#8b5cf6", "badge": "#a78bfa"},
    "Documentary": {"c1": "#0b1411", "c2": "#142621", "accent": "#14b8a6", "badge": "#2dd4bf"},
    "Drama": {"c1": "#140717", "c2": "#2b0f33", "accent": "#d946ef", "badge": "#e879f9"},
    "Fantasy": {"c1": "#070c1a", "c2": "#0e1a38", "accent": "#6366f1", "badge": "#818cf8"},
    "Film-Noir": {"c1": "#0a0a0a", "c2": "#1e1e1e", "accent": "#e2e8f0", "badge": "#cbd5e1"},
    "Horror": {"c1": "#170202", "c2": "#2e0505", "accent": "#dc2626", "badge": "#ef4444"},
    "Musical": {"c1": "#1a0418", "c2": "#3b0936", "accent": "#f43f5e", "badge": "#fb7185"},
    "Mystery": {"c1": "#090d1c", "c2": "#131b3b", "accent": "#3b82f6", "badge": "#60a5fa"},
    "Romance": {"c1": "#1c040d", "c2": "#3b091b", "accent": "#f43f5e", "badge": "#fb7185"},
    "Sci-Fi": {"c1": "#02121a", "c2": "#042436", "accent": "#06b6d4", "badge": "#22d3ee"},
    "Thriller": {"c1": "#120417", "c2": "#24082e", "accent": "#a855f7", "badge": "#c084fc"},
    "War": {"c1": "#171408", "c2": "#2e2710", "accent": "#ca8a04", "badge": "#eab308"},
    "Western": {"c1": "#1a0d05", "c2": "#361b0a", "accent": "#ea580c", "badge": "#f97316"},
}

DEFAULT_PALETTE = {"c1": "#141414", "c2": "#262626", "accent": "#e50914", "badge": "#ff3838"}

DIRECTORS_BY_GENRE = {
    "Action": ["Christopher Nolan", "George Miller", "Chad Stahelski", "Denis Villeneuve", "James Cameron"],
    "Sci-Fi": ["Ridley Scott", "Lana Wachowski", "Steven Spielberg", "Stanley Kubrick", "Denis Villeneuve"],
    "Drama": ["Martin Scorsese", "Paul Thomas Anderson", "Greta Gerwig", "David Fincher", "Frank Darabont"],
    "Romance": ["Richard Linklater", "Celine Song", "Woody Allen", "James Cameron", "Baz Luhrmann"],
    "Comedy": ["Taika Waititi", "Wes Anderson", "Edgar Wright", "Phil Lord", "Coen Brothers"],
    "Crime": ["Quentin Tarantino", "Francis Ford Coppola", "Martin Scorsese", "Michael Mann", "Bong Joon-ho"],
    "Horror": ["Ari Aster", "Jordan Peele", "Guillermo del Toro", "James Wan", "John Carpenter"],
    "Default": ["David Fincher", "Christopher Nolan", "Steven Spielberg", "Denis Villeneuve"],
}

ACTORS_BY_GENRE = {
    "Action": ["Keanu Reeves", "Tom Cruise", "Charlize Theron", "Christian Bale", "Sigourney Weaver"],
    "Sci-Fi": ["Harrison Ford", "Carrie-Anne Moss", "Matthew McConaughey", "Cillian Murphy", "Zoe Saldana"],
    "Drama": ["Morgan Freeman", "Tim Robbins", "Meryl Streep", "Leonardo DiCaprio", "Cate Blanchett"],
    "Romance": ["Kate Winslet", "Ethan Hawke", "Julie Delpy", "Ryan Gosling", "Emma Stone"],
    "Comedy": ["Bill Murray", "Steve Carell", "Emma Stone", "Paul Rudd", "Kristen Wiig"],
    "Crime": ["Al Pacino", "Robert De Niro", "Joe Pesci", "Samuel L. Jackson", "Harvey Keitel"],
    "Horror": ["Toni Collette", "Vera Farmiga", "Patrick Wilson", "Florence Pugh", "Bill Skarsgård"],
    "Default": ["Leonardo DiCaprio", "Christian Bale", "Meryl Streep", "Morgan Freeman", "Cate Blanchett"],
}

SYNOPSIS_TEMPLATES = [
    (
        "Released in {year}, '{title}' stands as an extraordinary {genre_str} masterpiece. "
        "When an unexpected sequence of events challenges everything they know, the protagonists "
        "must navigate high-stakes dilemmas, unearthing deeper truths about human resilience, courage, "
        "and fate in a rapidly changing world."
    ),
    (
        "In this captivating {year} {genre_str} classic, '{title}' immerses audiences in an atmospheric narrative "
        "filled with tension, unforgettable encounters, and profound revelations. As rival forces converge, "
        "our central characters are forced to reckon with their personal convictions and redefine their destiny."
    ),
    (
        "Set in {year}, '{title}' weaves a compelling {genre_str} tapestry of ambition, conflict, and redemption. "
        "Guided by sharp direction and striking performances, the film delves into the emotional core "
        "of its characters as they confront insurmountable odds and discover unexpected alliances."
    ),
    (
        "A critically celebrated {genre_str} journey from {year}, '{title}' explores the fragile boundaries "
        "between ambition and sacrifice. As secrets unravel and the clock ticks down, each choice carries "
        "seismic consequences, culminating in a breathless cinematic climax."
    ),
]


def _get_palette(genres: List[str]) -> Dict[str, str]:
    """Retrieve color palette based on first matching genre."""
    for g in genres:
        if g in GENRE_PALETTES:
            return GENRE_PALETTES[g]
    return DEFAULT_PALETTE


def _wrap_text(text: str, max_chars_per_line: int = 18) -> List[str]:
    """Break title into multiple lines for SVG rendering."""
    words = text.split()
    lines: List[str] = []
    current_line: List[str] = []
    current_len = 0

    for word in words:
        if current_len + len(word) + (1 if current_line else 0) <= max_chars_per_line:
            current_line.append(word)
            current_len += len(word) + (1 if len(current_line) > 1 else 0)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_len = len(word)

    if current_line:
        lines.append(" ".join(current_line))
    return lines[:3]  # Limit to 3 lines max


def _normalize_genres(genres: Optional[Any]) -> List[str]:
    """Safely convert genres argument (list, ndarray, or None) to list of strings."""
    if genres is None:
        return []
    if hasattr(genres, "tolist"):
        return [str(g) for g in genres.tolist()]
    if isinstance(genres, (list, tuple)):
        return [str(g) for g in genres]
    return [str(genres)]


def generate_svg_poster(
    title: str,
    year: Optional[int] = None,
    genres: Optional[Any] = None,
    movie_id: Optional[int] = None,
) -> str:
    """Generate a high-contrast, modern SVG movie poster as a base64 Data URI."""
    raw_genres = _normalize_genres(genres)
    genres_list = raw_genres if len(raw_genres) > 0 else ["Movie"]
    palette = _get_palette(genres_list)
    year_str = str(year) if year else ""
    genre_display = " • ".join(genres_list[:2])

    # Hash for deterministic seed
    seed = int(hashlib.md5(f"{title}_{year}_{movie_id}".encode()).hexdigest(), 16)
    score = round(3.5 + (seed % 15) * 0.1, 1)

    wrapped_lines = _wrap_text(title, max_chars_per_line=16)
    c1 = palette["c1"]
    c2 = palette["c2"]
    accent = palette["accent"]
    badge_bg = palette["badge"]

    # Calculate y-positions for title tspans
    line_spacing = 30
    title_start_y = 190 - (len(wrapped_lines) - 1) * 15

    tspans = ""
    for idx, line in enumerate(wrapped_lines):
        y_pos = title_start_y + (idx * line_spacing)
        safe_line = html.escape(line)
        tspans += f'<text x="150" y="{y_pos}" text-anchor="middle" fill="#FFFFFF" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-weight="800" font-size="22" letter-spacing="0.5">{safe_line}</text>'

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 450" width="300" height="450">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c1}" />
      <stop offset="60%" stop-color="{c2}" />
      <stop offset="100%" stop-color="#0a0a0a" />
    </linearGradient>
    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{accent}" />
      <stop offset="100%" stop-color="{badge_bg}" />
    </linearGradient>
    <linearGradient id="vignette" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#000000" stop-opacity="0.3" />
      <stop offset="50%" stop-color="#000000" stop-opacity="0.0" />
      <stop offset="100%" stop-color="#000000" stop-opacity="0.75" />
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="300" height="450" fill="url(#bgGrad)" />
  <rect width="300" height="450" fill="url(#vignette)" />

  <!-- Subtle Decorative Grid Lines -->
  <line x1="20" y1="20" x2="280" y2="20" stroke="{accent}" stroke-opacity="0.4" stroke-width="1.5" />
  <line x1="20" y1="430" x2="280" y2="430" stroke="{accent}" stroke-opacity="0.4" stroke-width="1.5" />

  <!-- Cinematch Logo / Top Banner -->
  <text x="150" y="42" text-anchor="middle" fill="{accent}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-weight="900" font-size="12" letter-spacing="3">CINEMATCH</text>

  <!-- Film Clapper / Frame Icon Graphic -->
  <circle cx="150" cy="100" r="34" fill="{c2}" stroke="{accent}" stroke-width="2" stroke-opacity="0.6" />
  <polygon points="142,88 164,100 142,112" fill="{accent}" />

  <!-- Title -->
  {tspans}

  <!-- Year & Rating Badges -->
  <g transform="translate(150, 310)">
    <!-- Genre Pill -->
    <rect x="-80" y="-14" width="160" height="26" rx="13" fill="#1f1f1f" stroke="{accent}" stroke-width="1" stroke-opacity="0.8" />
    <text x="0" y="4" text-anchor="middle" fill="#E5E5E5" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-weight="600" font-size="11">{html.escape(genre_display)}</text>
  </g>

  <!-- Year & Match Score Footer -->
  <g transform="translate(150, 370)">
    <text x="-40" y="0" text-anchor="middle" fill="#A3A3A3" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-weight="500" font-size="13">{html.escape(year_str)}</text>
    <text x="0" y="0" text-anchor="middle" fill="#737373" font-size="13">•</text>
    <text x="40" y="0" text-anchor="middle" fill="#46d369" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-weight="700" font-size="13">★ {score}</text>
  </g>

  <!-- Bottom Accent Stripe -->
  <rect x="0" y="445" width="300" height="5" fill="url(#accentGrad)" />
</svg>"""

    encoded = base64.b64encode(svg_content.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def generate_svg_backdrop(
    title: str,
    year: Optional[int] = None,
    genres: Optional[Any] = None,
    movie_id: Optional[int] = None,
) -> str:
    """Generate a wide 16:9 cinematic SVG backdrop as a base64 Data URI."""
    raw_genres = _normalize_genres(genres)
    genres_list = raw_genres if len(raw_genres) > 0 else ["Movie"]
    palette = _get_palette(genres_list)
    year_str = str(year) if year else ""
    genre_display = " • ".join(genres_list)
    safe_title = html.escape(title)

    c1 = palette["c1"]
    c2 = palette["c2"]
    accent = palette["accent"]

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
  <defs>
    <linearGradient id="wideBgGrad" x1="0%" y1="0%" x2="100%" y2="80%">
      <stop offset="0%" stop-color="{c1}" />
      <stop offset="45%" stop-color="{c2}" />
      <stop offset="100%" stop-color="#0a0a0a" />
    </linearGradient>
    <radialGradient id="glow" cx="65%" cy="35%" r="60%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.35" />
      <stop offset="50%" stop-color="{c2}" stop-opacity="0.1" />
      <stop offset="100%" stop-color="#000000" stop-opacity="0" />
    </radialGradient>
    <linearGradient id="overlayVignette" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#000000" stop-opacity="0.4" />
      <stop offset="60%" stop-color="#000000" stop-opacity="0.2" />
      <stop offset="100%" stop-color="#141414" stop-opacity="0.95" />
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="1280" height="720" fill="url(#wideBgGrad)" />
  <rect width="1280" height="720" fill="url(#glow)" />
  <rect width="1280" height="720" fill="url(#overlayVignette)" />

  <!-- Ambient Cinema Spotlight Rings -->
  <circle cx="850" cy="260" r="180" fill="none" stroke="{accent}" stroke-width="1.5" stroke-opacity="0.2" />
  <circle cx="850" cy="260" r="280" fill="none" stroke="{accent}" stroke-width="1.0" stroke-opacity="0.1" />

  <!-- Cinematch Watermark -->
  <text x="80" y="100" fill="{accent}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-weight="900" font-size="20" letter-spacing="4">CINEMATCH ORIGINAL</text>

  <!-- Title & Metadata on Lower Left -->
  <g transform="translate(80, 520)">
    <!-- Movie Title -->
    <text x="0" y="0" fill="#FFFFFF" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-weight="900" font-size="52" letter-spacing="-0.5">{safe_title}</text>
    
    <!-- Badges Row -->
    <g transform="translate(0, 45)">
      <rect x="0" y="-22" width="65" height="30" rx="4" fill="#333333" />
      <text x="32" y="-2" text-anchor="middle" fill="#FFFFFF" font-family="sans-serif" font-weight="700" font-size="16">{html.escape(year_str)}</text>
      
      <text x="85" y="-2" fill="#46d369" font-family="sans-serif" font-weight="800" font-size="16">98% Match</text>
      <text x="195" y="-2" fill="#A3A3A3" font-family="sans-serif" font-weight="500" font-size="16">{html.escape(genre_display)}</text>
    </g>
  </g>

  <!-- Bottom Accent Stripe -->
  <rect x="0" y="714" width="1280" height="6" fill="{accent}" />
</svg>"""

    encoded = base64.b64encode(svg_content.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def generate_deterministic_synopsis(
    title: str,
    year: Optional[int] = None,
    genres: Optional[Any] = None,
    movie_id: Optional[int] = None,
) -> str:
    """Generate a rich, context-aware synopsis based on movie properties."""
    raw_genres = _normalize_genres(genres)
    genres_list = raw_genres if len(raw_genres) > 0 else ["Cinema"]
    genre_str = ", ".join(genres_list)
    year_val = year or 2000

    seed = int(hashlib.md5(f"synopsis_{title}_{year}_{movie_id}".encode()).hexdigest(), 16)
    template = SYNOPSIS_TEMPLATES[seed % len(SYNOPSIS_TEMPLATES)]

    return template.format(
        title=title,
        year=year_val,
        genre_str=genre_str,
    )


def generate_deterministic_credits(
    genres: Optional[Any] = None,
    movie_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Generate deterministic director and cast members based on genres."""
    raw_genres = _normalize_genres(genres)
    genres_list = raw_genres if len(raw_genres) > 0 else ["Default"]
    primary_genre = genres_list[0] if genres_list else "Default"

    directors = DIRECTORS_BY_GENRE.get(primary_genre, DIRECTORS_BY_GENRE["Default"])
    actors = ACTORS_BY_GENRE.get(primary_genre, ACTORS_BY_GENRE["Default"])

    seed = int(hashlib.md5(f"credits_{primary_genre}_{movie_id}".encode()).hexdigest(), 16)
    director = directors[seed % len(directors)]
    # Pick 3-4 cast members deterministically
    start_idx = seed % len(actors)
    cast_list = [actors[(start_idx + i) % len(actors)] for i in range(min(4, len(actors)))]

    return {
        "director": director,
        "cast": cast_list,
        "runtime": 90 + ((seed % 9) * 10),  # 90 to 170 mins
        "vote_average": round(3.2 + ((seed % 17) * 0.1), 1),
        "vote_count": 500 + ((seed % 450) * 10),
    }


class TMDBService:
    """TMDB API Client using API Read Access Token (Bearer auth) with seamless offline fallback."""

    def __init__(self, read_token: Optional[str] = None, api_key: Optional[str] = None):
        # Support both read_token and api_key parameter names
        self.read_token = (
            read_token
            if read_token is not None
            else (api_key if api_key is not None else settings.effective_tmdb_read_token)
        )
        self.base_url = settings.tmdb_base_url
        self.image_base_url = settings.tmdb_image_base_url
        self.timeout = 3.0  # seconds

    @property
    def api_key(self) -> Optional[str]:
        """Backward-compatible alias for read_token."""
        return self.read_token

    @property
    def is_offline(self) -> bool:
        """Check if TMDB client should run in pure offline fallback mode."""
        if not self.read_token:
            return True
        key = self.read_token.strip().lower()
        return key in {"", "apikey", "dummy", "placeholder", "test", "none"}

    def _get_headers(self) -> Dict[str, str]:
        """Generate HTTP headers with TMDB API Read Access Token as Bearer token."""
        headers = {
            "accept": "application/json",
            "User-Agent": "CineMatch/1.0",
        }
        if not self.is_offline and self.read_token:
            headers["Authorization"] = f"Bearer {self.read_token}"
        return headers

    def get_fallback_metadata(
        self,
        title: str,
        year: Optional[int] = None,
        genres: Optional[List[str]] = None,
        movie_id: Optional[int] = None,
        tmdb_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive deterministic fallback metadata."""
        genres_list = genres or []
        poster_uri = generate_svg_poster(title, year=year, genres=genres_list, movie_id=movie_id)
        backdrop_uri = generate_svg_backdrop(title, year=year, genres=genres_list, movie_id=movie_id)
        synopsis = generate_deterministic_synopsis(title, year=year, genres=genres_list, movie_id=movie_id)
        credits_info = generate_deterministic_credits(genres=genres_list, movie_id=movie_id)

        # Deterministic tmdb_id if none provided
        calc_tmdb_id = tmdb_id or (movie_id + 100000 if movie_id else 100001)

        return {
            "tmdb_id": calc_tmdb_id,
            "title": title,
            "year": year,
            "genres": genres_list,
            "synopsis": synopsis,
            "overview": synopsis,
            "poster_path": poster_uri,
            "backdrop_path": backdrop_uri,
            "vote_average": credits_info["vote_average"],
            "vote_count": credits_info["vote_count"],
            "director": credits_info["director"],
            "cast": credits_info["cast"],
            "runtime": credits_info["runtime"],
        }

    def search_movies_sync(self, query: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search movies via TMDB API using API Read Access Token (Bearer auth)."""
        if self.is_offline:
            # Generate deterministic fallback search result
            meta = self.get_fallback_metadata(title=query, year=year, genres=["Action", "Drama"])
            return [meta]

        try:
            params: Dict[str, str] = {"query": query}
            if year:
                params["year"] = str(year)
            # If the provided key is a legacy 32-char hex string rather than a JWT bearer token, also include as query param
            if self.read_token and len(self.read_token) == 32 and not self.read_token.startswith("eyJ"):
                params["api_key"] = self.read_token

            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(
                    f"{self.base_url}/search/movie",
                    params=params,
                    headers=self._get_headers(),
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    return results
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            logger.warning("TMDB search failed (%s), using offline fallback", exc)

        meta = self.get_fallback_metadata(title=query, year=year, genres=["Action", "Drama"])
        return [meta]

    def get_movie_details_sync(self, tmdb_id: int) -> Dict[str, Any]:
        """Fetch movie details by TMDB ID using API Read Access Token."""
        if self.is_offline:
            return self.get_fallback_metadata(title=f"Movie {tmdb_id}", tmdb_id=tmdb_id)

        try:
            params: Dict[str, str] = {"append_to_response": "credits,videos"}
            if self.read_token and len(self.read_token) == 32 and not self.read_token.startswith("eyJ"):
                params["api_key"] = self.read_token

            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(
                    f"{self.base_url}/movie/{tmdb_id}",
                    params=params,
                    headers=self._get_headers(),
                )
                if resp.status_code == 200:
                    return resp.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            logger.warning("TMDB get_movie_details failed (%s), using offline fallback", exc)

        return self.get_fallback_metadata(title=f"Movie {tmdb_id}", tmdb_id=tmdb_id)

    async def get_movie_details_async(self, tmdb_id: int) -> Dict[str, Any]:
        """Asynchronous version of get_movie_details using API Read Access Token."""
        if self.is_offline:
            return self.get_fallback_metadata(title=f"Movie {tmdb_id}", tmdb_id=tmdb_id)

        try:
            params: Dict[str, str] = {"append_to_response": "credits,videos"}
            if self.read_token and len(self.read_token) == 32 and not self.read_token.startswith("eyJ"):
                params["api_key"] = self.read_token

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/movie/{tmdb_id}",
                    params=params,
                    headers=self._get_headers(),
                )
                if resp.status_code == 200:
                    return resp.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            logger.warning("Async TMDB get_movie_details failed (%s), using offline fallback", exc)

        return self.get_fallback_metadata(title=f"Movie {tmdb_id}", tmdb_id=tmdb_id)

    def enrich_movie(
        self,
        title: str,
        year: Optional[int] = None,
        genres: Optional[List[str]] = None,
        movie_id: Optional[int] = None,
        tmdb_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Convenience method to enrich movie with TMDB data or high-fidelity fallback."""
        if self.is_offline or tmdb_id is None:
            return self.get_fallback_metadata(
                title=title,
                year=year,
                genres=genres,
                movie_id=movie_id,
                tmdb_id=tmdb_id,
            )

        # Attempt to fetch live details if tmdb_id is given
        details = self.get_movie_details_sync(tmdb_id)
        if "overview" in details:
            poster = (
                f"{self.image_base_url}/w500{details['poster_path']}"
                if details.get("poster_path")
                else generate_svg_poster(title, year=year, genres=genres, movie_id=movie_id)
            )
            backdrop = (
                f"{self.image_base_url}/original{details['backdrop_path']}"
                if details.get("backdrop_path")
                else generate_svg_backdrop(title, year=year, genres=genres, movie_id=movie_id)
            )
            return {
                "tmdb_id": details.get("id", tmdb_id),
                "title": details.get("title", title),
                "year": year,
                "genres": [g["name"] for g in details.get("genres", [])] or (genres or []),
                "synopsis": details.get("overview") or generate_deterministic_synopsis(title, year, genres, movie_id),
                "overview": details.get("overview") or generate_deterministic_synopsis(title, year, genres, movie_id),
                "poster_path": poster,
                "backdrop_path": backdrop,
                "vote_average": details.get("vote_average", 4.0),
                "vote_count": details.get("vote_count", 100),
                "director": None,
                "cast": None,
                "runtime": details.get("runtime"),
            }

        return self.get_fallback_metadata(
            title=title,
            year=year,
            genres=genres,
            movie_id=movie_id,
            tmdb_id=tmdb_id,
        )


tmdb_service = TMDBService()
