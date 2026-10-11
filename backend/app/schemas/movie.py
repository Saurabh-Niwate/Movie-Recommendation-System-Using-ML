from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.services.tmdb import resolve_poster_url, resolve_backdrop_url, TMDB_ID_MAP


class MovieSummary(BaseModel):
    id: int
    movie_id: Optional[int] = None
    movie_lens_id: Optional[int] = None
    tmdb_id: Optional[int] = None
    title: str
    title_raw: Optional[str] = None
    year: Optional[int] = None
    genres: List[str] = []
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: int = 0
    item_idx: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_movie_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "movie_id" not in data and "id" in data:
                data["movie_id"] = data["id"]
            elif "id" not in data and "movie_id" in data:
                data["id"] = data["movie_id"]
        return data

    @model_validator(mode="after")
    def sync_fields_and_sanitize_media(self) -> "MovieSummary":
        if self.movie_id is None:
            self.movie_id = self.id

        mid = self.movie_id or self.id or 1
        # Resolve canonical tmdb_id if missing or synthetic
        if self.tmdb_id is None or self.tmdb_id >= 100000:
            if mid in TMDB_ID_MAP:
                self.tmdb_id = TMDB_ID_MAP[mid]
            elif self.tmdb_id is None:
                self.tmdb_id = mid

        # Sanitize image paths ensuring real TMDB CDN or Stitch hosted stills with zero SVG
        self.poster_path = resolve_poster_url(
            movie_id=mid,
            tmdb_id=self.tmdb_id,
            raw_path=self.poster_path,
        )
        self.backdrop_path = resolve_backdrop_url(
            movie_id=mid,
            tmdb_id=self.tmdb_id,
            raw_path=self.backdrop_path,
        )
        return self


class MovieDetail(MovieSummary):
    synopsis: Optional[str] = None
    overview: Optional[str] = None
    director: Optional[str] = None
    cast: Optional[Any] = None
    runtime: Optional[int] = None
    match_percent: Optional[int] = None


class MovieSearchResponse(BaseModel):
    items: List[MovieSummary]
    total: int


class MovieTrailerResponse(BaseModel):
    movie_id: Optional[int] = Field(None, description="Database movie ID if available")
    tmdb_id: int = Field(..., description="The Movie Database identifier")
    title: str = Field(..., description="Movie title")
    key: str = Field(..., min_length=5, description="YouTube video ID key")
    site: str = Field("YouTube", description="Video hosting provider")
    embed_url: str = Field(..., description="Direct YouTube iframe embed URL")
    watch_url: str = Field(..., description="Direct YouTube watch URL")
