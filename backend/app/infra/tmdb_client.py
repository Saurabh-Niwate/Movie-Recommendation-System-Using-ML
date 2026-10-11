"""Forwarder to app.services.tmdb."""
from app.services.tmdb import (
    TMDBService,
    tmdb_service,
    resolve_poster_url,
    resolve_backdrop_url,
    generate_svg_poster,
    generate_svg_backdrop,
    generate_deterministic_synopsis,
    generate_deterministic_credits,
    TMDB_ID_MAP,
    TRAILER_MAP,
)

__all__ = [
    "TMDBService",
    "tmdb_service",
    "resolve_poster_url",
    "resolve_backdrop_url",
    "generate_svg_poster",
    "generate_svg_backdrop",
    "generate_deterministic_synopsis",
    "generate_deterministic_credits",
    "TMDB_ID_MAP",
    "TRAILER_MAP",
]
