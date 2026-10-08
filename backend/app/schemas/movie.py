from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict


class MovieSummary(BaseModel):
    id: int
    movie_lens_id: Optional[int] = None
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


class MovieDetail(MovieSummary):
    synopsis: Optional[str] = None
    overview: Optional[str] = None
    director: Optional[str] = None
    cast: Optional[Any] = None
    runtime: Optional[int] = None
    tmdb_id: Optional[int] = None
    match_percent: Optional[int] = None


class MovieSearchResponse(BaseModel):
    items: List[MovieSummary]
    total: int
