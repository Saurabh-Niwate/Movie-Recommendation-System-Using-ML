from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.movie import MovieSummary


class RatingCreate(BaseModel):
    movie_id: int
    rating: float = Field(..., ge=0.5, le=5.0)


class ProfileRatingCreate(BaseModel):
    profile_id: Optional[str] = None
    movie_id: int
    rating: float = Field(..., ge=0.5, le=5.0)


class RatingResponse(BaseModel):
    status: str = "ok"
    ratings_count: int
    unlocked: bool
    fold_in_ms: Optional[float] = None
    message: Optional[str] = None


class RatingItem(BaseModel):
    id: int
    profile_id: str
    movie_id: int
    rating: float
    item_idx: Optional[int] = None
    movie: Optional[MovieSummary] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
