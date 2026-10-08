from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

logger = logging.getLogger("cinematch.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager: preloads schema and ML model artifacts."""
    logger.info("Initializing CineMatch application...")
    try:
        ensure_schema_exists(engine)
        logger.info("Database schema cinematch verified.")
    except Exception as e:
        logger.warning(f"Could not verify schema on engine: {e}")

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
    app.include_router(profiles_router, prefix=f"{pfx}/profiles")
    app.include_router(movies_router, prefix=f"{pfx}/movies")
    app.include_router(ratings_router, prefix=f"{pfx}/ratings")
    app.include_router(recommendations_router, prefix=f"{pfx}/recommendations")
    app.include_router(model_lab_router, prefix=f"{pfx}/model-lab")
    app.include_router(tmdb_router, prefix=f"{pfx}/tmdb")

