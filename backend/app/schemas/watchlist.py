from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, model_validator


class WatchlistItemResponse(BaseModel):
    id: int
    movie_id: Optional[int] = None
    title: str
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    release_year: Optional[int] = None
    year: Optional[int] = None
    genres: List[str] = []
    vote_average: Optional[float] = None
    vote_count: Optional[int] = 0
    added_at: Optional[datetime] = None
    synopsis: Optional[str] = None
    overview: Optional[str] = None
    tmdb_id: Optional[int] = None
    director: Optional[str] = None
    runtime: Optional[int] = None
    list_type: str = "watchlist"

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def sync_incoming_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "movie_id" not in data and "id" in data:
                data["movie_id"] = data["id"]
            elif "id" not in data and "movie_id" in data:
                data["id"] = data["movie_id"]

            if "release_year" not in data and "year" in data:
                data["release_year"] = data["year"]
            elif "year" not in data and "release_year" in data:
                data["year"] = data["release_year"]
        return data

    @model_validator(mode="after")
    def sync_resolved_keys(self) -> "WatchlistItemResponse":
        if self.movie_id is None:
            self.movie_id = self.id
        if self.release_year is None and self.year is not None:
            self.release_year = self.year
        elif self.year is None and self.release_year is not None:
            self.year = self.release_year
        return self


class WatchlistActionResponse(BaseModel):
    status: str
    profile_id: str
    movie_id: int
    message: Optional[str] = None


class WatchlistCreateRequest(BaseModel):
    movie_id: Optional[int] = None
    id: Optional[int] = None
    profile_id: Optional[str] = None
    list_type: Optional[str] = "watchlist"

    @model_validator(mode="before")
    @classmethod
    def populate_movie_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "movie_id" not in data and "id" in data:
                data["movie_id"] = data["id"]
            elif "id" not in data and "movie_id" in data:
                data["id"] = data["movie_id"]
        return data
