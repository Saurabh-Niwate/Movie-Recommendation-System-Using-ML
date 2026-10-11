from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, ensure_schema_exists
from app.infra.model_registry import get_model_registry
from app.routers import (
    profiles_router,
    movies_router,
    ratings_router,
    recommendations_router,
    model_lab_router,
    tmdb_router,
)
from app.routers.auth import router as auth_router
from app.routers.watchlist import router as watchlist_router

logger = logging.getLogger("cinematch.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager: preloads schema, auto-seeds DB, and ML model artifacts."""
    logger.info("Initializing CineMatch application...")
    try:
        ensure_schema_exists(engine)
        logger.info("Database schema and tables verified (engine=%s).", engine.dialect.name)
    except Exception as e:
        logger.warning("Could not verify schema on engine: %s", e)

    # Auto-seed database if empty on startup
    try:
        from app.core.database import SessionLocal
        from app.models.profile import Profile
        from app.models.movie import Movie
        from app.models.user import User
        from app.services.auth_service import auth_service
        try:
            from scripts.seed import seed_database
        except ImportError:
            from backend.scripts.seed import seed_database

        with SessionLocal() as db:
            profile_count = db.query(Profile).count()
            movie_count = db.query(Movie).count()
            user_count = db.query(User).count()
            logger.info("Database status on startup: %d profiles, %d movies, %d users", profile_count, movie_count, user_count)
            if profile_count == 0 or movie_count == 0:
                logger.info(
                    "Auto-seeding required (profile_count=%d, movie_count=%d). Triggering pipeline...",
                    profile_count,
                    movie_count,
                )
                seed_database(db=db, force=False)
                logger.info("Auto-seeding completed successfully on startup.")
            else:
                logger.info("Database already seeded. Skipping auto-seeding.")

            if user_count == 0:
                auth_service.seed_default_users(db)
                logger.info("Default user accounts seeded.")
    except Exception as exc:
        logger.error("Auto-seeding pipeline encountered an error: %s", exc, exc_info=True)

    # Pre-load ML model artifacts on startup
    try:
        reg = get_model_registry()
        logger.info(
            "Model registry loaded: FunkSVD (%d factors), ItemKNN (%d items)",
            reg.funk_svd.n_factors if reg.funk_svd else 0,
            reg.item_knn.n_items if reg.item_knn else 0,
        )
    except Exception as e:
        logger.error(f"Failed to load model registry on startup: {e}")

    yield
    logger.info("CineMatch application shutting down.")


app = FastAPI(
    title="CineMatch Movie Recommender API",
    description="Full-stack movie recommendation system replicating Furtado & Singh (2020) with Item-KNN, Funk-SVD, Association Rules, and online fold-in.",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for browser React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"], include_in_schema=False)
@app.get("/api/v1/health", tags=["Health"], include_in_schema=False)
def health_check():
    reg = get_model_registry()
    return {
        "status": "ok",
        "service": "cinematch-backend",
        "version": "0.1.0",
        "models_loaded": reg.is_loaded,
    }


# Dual router mounting: both /api/v1 and /api prefixes
prefixes = ["/api/v1", "/api"]

for pfx in prefixes:
    app.include_router(auth_router, prefix=f"{pfx}/auth")
    app.include_router(profiles_router, prefix=f"{pfx}/profiles")
    app.include_router(movies_router, prefix=f"{pfx}/movies")
    app.include_router(ratings_router, prefix=f"{pfx}/ratings")
    app.include_router(recommendations_router, prefix=f"{pfx}/recommendations")
    app.include_router(model_lab_router, prefix=f"{pfx}/model-lab")
    app.include_router(tmdb_router, prefix=f"{pfx}/tmdb")
    app.include_router(watchlist_router, prefix=f"{pfx}")


from starlette.exceptions import HTTPException as StarletteHTTPException


class SPAStaticFiles(StaticFiles):
    """Custom StaticFiles handler providing HTML5 pushState fallback for single-page apps."""
    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
            if response.status_code == 404 and not path.startswith("api/"):
                return await super().get_response("index.html", scope)
            return response
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and not path.startswith("api/"):
                return await super().get_response("index.html", scope)
            raise


# Static file mounting for frontend/dist on / when the directory exists (without crashing if not yet built)
try:
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dist.is_dir() and (frontend_dist / "index.html").is_file():
        app.mount("/", SPAStaticFiles(directory=str(frontend_dist), html=True), name="frontend")
        logger.info("Mounted static frontend assets with SPA fallback from %s", frontend_dist)
    else:
        logger.info("Frontend dist directory not found at %s. Skipping static mount.", frontend_dist)
except Exception as e:
    logger.warning("Error attempting to mount static files: %s", e)
