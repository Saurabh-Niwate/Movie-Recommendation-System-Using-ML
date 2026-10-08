from app.routers.profiles import router as profiles_router
from app.routers.movies import router as movies_router
from app.routers.ratings import router as ratings_router
from app.routers.recommendations import router as recommendations_router
from app.routers.model_lab import router as model_lab_router
from app.routers.tmdb import router as tmdb_router

__all__ = [
    "profiles_router",
    "movies_router",
    "ratings_router",
    "recommendations_router",
    "model_lab_router",
    "tmdb_router",
]

