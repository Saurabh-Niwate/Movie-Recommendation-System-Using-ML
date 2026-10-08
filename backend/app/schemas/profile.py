from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, model_validator

DEFAULT_PROFILE_GENRES = {
    "neel": ["Action", "Sci-Fi", "Adventure"],
    "nitin": ["Drama", "Romance"],
    "mukesh": [],
}

DEFAULT_PROFILE_ACCENTS = {
    "neel": "from-cyan-600 to-blue-700",
    "nitin": "from-purple-600 to-pink-700",
    "mukesh": "from-amber-600 to-emerald-700",
}


class ProfileBase(BaseModel):
    id: str
    name: str
    avatar: str
    bio: Optional[str] = None
    taste_cluster: Optional[str] = None
    is_demo: bool = False
    genres: List[str] = []
    color_accent: Optional[str] = None


class ProfileResponse(ProfileBase):
    ratings_count: int
    is_cold_start: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def populate_defaults(self) -> "ProfileResponse":
        if not self.genres:
            self.genres = DEFAULT_PROFILE_GENRES.get(self.id, [])
        if not self.color_accent:
            self.color_accent = DEFAULT_PROFILE_ACCENTS.get(self.id, "from-zinc-700 to-zinc-900")
        return self


class ProfileDetailResponse(ProfileResponse):
    user_idx: Optional[int] = None

