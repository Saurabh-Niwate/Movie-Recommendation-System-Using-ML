from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ConvergenceEpoch(BaseModel):
    epoch: int
    train_loss: float
    val_rmse: float


class ConvergenceResponse(BaseModel):
    algorithm: str
    best_epoch: int
    training_time_sec: float
    epochs: List[ConvergenceEpoch]


class CompareItem(BaseModel):
    movie_id: int
    title: str
    genres: List[str] = []
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    score: float
    match_percent: int


class SideBySideCompareResponse(BaseModel):
    profile_id: str
    item_knn: List[CompareItem]
    funk_svd: List[CompareItem]


class LatentFactor(BaseModel):
    factor_index: int
    user_val: float
    item_val: float
    product: float


class FunkSVDExplainResponse(BaseModel):
    model: str = "funk_svd"
    profile_id: str
    movie_id: int
    title: str
    mu: float
    user_bias: float
    item_bias: float
    dot_product: float
    latent_breakdown: List[LatentFactor]
    predicted_score: float
    match_percent: int


class NeighborContribution(BaseModel):
    movie_id: int
    item_idx: int
    title: str
    similarity: float
    user_rating: float
    contribution: float


class ItemKNNExplainResponse(BaseModel):
    model: str = "item_knn"
    profile_id: str
    movie_id: int
    title: str
    user_mean: float
    neighbors: List[NeighborContribution]
    predicted_score: float
    match_percent: int
