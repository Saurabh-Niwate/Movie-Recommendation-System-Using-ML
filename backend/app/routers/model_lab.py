from typing import Dict, Any, Union
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.model_lab import (
    ConvergenceResponse,
    SideBySideCompareResponse,
    FunkSVDExplainResponse,
    ItemKNNExplainResponse,
)
from app.services.model_lab_service import model_lab_service

router = APIRouter(tags=["Model Lab"])


@router.get("/leaderboard")
def get_leaderboard():
    """Retrieve model evaluation leaderboard metrics from artifacts/v1/metrics.json."""
    return model_lab_service.get_leaderboard()


@router.get("/convergence", response_model=ConvergenceResponse)
def get_convergence():
    """Retrieve Funk-SVD training convergence curves (train loss and validation RMSE per epoch)."""
    return model_lab_service.get_convergence()


@router.get("/compare", response_model=SideBySideCompareResponse)
def compare_models(
    profile_id: str = Query("neel", description="Profile ID to compare recommendations for"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Retrieve side-by-side Top-10 recommendations from Item-KNN vs Funk-SVD."""
    return model_lab_service.compare_models(db, profile_id=profile_id, limit=limit)


@router.get(
    "/explain",
    response_model=Union[FunkSVDExplainResponse, ItemKNNExplainResponse],
)
def explain_prediction(
    profile_id: str = Query(..., description="Profile ID"),
    movie_id: int = Query(..., description="MovieLens Movie ID"),
    model: str = Query("funk_svd", description="Model algorithm: funk_svd or item_knn"),
    db: Session = Depends(get_db),
):
    """Return mathematical explainability breakdown of predicted rating."""
    return model_lab_service.explain_prediction(
        db=db,
        profile_id=profile_id,
        movie_id=movie_id,
        model_name=model,
    )
