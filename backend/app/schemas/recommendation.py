from typing import List, Optional, Any
from pydantic import BaseModel
from app.schemas.movie import MovieSummary


class RecommendationItem(BaseModel):
    id: int
    movie_lens_id: Optional[int] = None
    title: str
    year: Optional[int] = None
    genres: List[str] = []
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    synopsis: Optional[str] = None
    overview: Optional[str] = None
    vote_average: Optional[float] = None
    score: float
    match_percent: int
    algorithm: Optional[str] = None
    item_idx: Optional[int] = None


class BecauseYouLikedResponse(BaseModel):
    source_movie: MovieSummary
    recommendations: List[RecommendationItem]


class AlsoWatchedItem(BaseModel):
    id: int
    title: str
    genres: List[str] = []
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    lift: float
    cooccurrence: int


class GenreCarousel(BaseModel):
    genre: str
    movies: List[RecommendationItem]
