from pathlib import Path
import json
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import scipy.sparse as sp

from recsys.models.funk_svd import FunkSVD
from recsys.models.item_knn import ItemKNN
from recsys.models.association_rules import AssociationRules
from recsys.models.popularity import PopularityRecommender


def resolve_artifacts_dir() -> Path:
    """Resolve artifacts/v1 directory relative to file location or cwd."""
    cand = Path(__file__).resolve().parents[3] / "artifacts" / "v1"
    if cand.is_dir():
        return cand
    cand_cwd = Path.cwd() / "artifacts" / "v1"
    if cand_cwd.is_dir():
        return cand_cwd
    cand_parent = Path.cwd().parent / "artifacts" / "v1"
    if cand_parent.is_dir():
        return cand_parent
    return cand


class ModelRegistry:
    """In-memory singleton registry holding trained recommender models and mappings."""

    def __init__(self, artifacts_dir: Optional[Path] = None):
        self.artifacts_dir = artifacts_dir or resolve_artifacts_dir()
        self.funk_svd: Optional[FunkSVD] = None
        self.item_knn: Optional[ItemKNN] = None
        self.associations: Optional[AssociationRules] = None
        self.popularity: Optional[PopularityRecommender] = None
        self.id_maps: Dict[str, Any] = {}
        self.profiles_config: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}
        self.convergence: Dict[str, Any] = {}

        # Mappings
        self.movie_id_to_item_idx: Dict[int, int] = {}
        self.item_idx_to_movie_id: Dict[int, int] = {}
        self.user_id_to_user_idx: Dict[int, int] = {}
        self.user_idx_to_user_id: Dict[int, int] = {}

        # Cached folded-in user vectors: profile_id -> (b_u, p_u)
        self._user_vectors: Dict[str, Tuple[float, np.ndarray]] = {}

        self.is_loaded: bool = False

    def load_all(self) -> "ModelRegistry":
        """Load all model artifacts and companion metadata from disk."""
        if self.is_loaded:
            return self

        art_dir = self.artifacts_dir
        if not art_dir.exists():
            raise FileNotFoundError(f"Artifacts directory not found: {art_dir}")

        # 1. Funk-SVD
        funk_path = art_dir / "funk_svd.npz"
        if funk_path.exists():
            self.funk_svd = FunkSVD.load(funk_path)

        # 2. Item-KNN
        knn_path = art_dir / "item_knn.npz"
        if knn_path.exists():
            self.item_knn = ItemKNN.load(knn_path)

        # 3. Association Rules
        assoc_parquet = art_dir / "associations.parquet"
        assoc_json = art_dir / "associations.json"
        if assoc_parquet.exists():
            self.associations = AssociationRules.load(assoc_parquet)
        elif assoc_json.exists():
            self.associations = AssociationRules.load(assoc_json)

        # 4. Bayesian Popularity
        pop_path = art_dir / "popularity.json"
        if pop_path.exists():
            self.popularity = PopularityRecommender.load(pop_path)

        # 5. ID maps
        id_maps_path = art_dir / "id_maps.json"
        if id_maps_path.exists():
            with open(id_maps_path, "r", encoding="utf-8") as f:
                self.id_maps = json.load(f)
            self.movie_id_to_item_idx = {
                int(k): int(v) for k, v in self.id_maps.get("movie_id_to_item_idx", {}).items()
            }
            self.item_idx_to_movie_id = {
                int(k): int(v) for k, v in self.id_maps.get("item_idx_to_movie_id", {}).items()
            }
            self.user_id_to_user_idx = {
                int(k): int(v) for k, v in self.id_maps.get("user_id_to_user_idx", {}).items()
            }
            self.user_idx_to_user_id = {
                int(k): int(v) for k, v in self.id_maps.get("user_idx_to_user_id", {}).items()
            }

        # 6. Profiles config
        prof_path = art_dir / "profiles.json"
        if prof_path.exists():
            with open(prof_path, "r", encoding="utf-8") as f:
                self.profiles_config = json.load(f)

        # 7. Metrics (leaderboard)
        metrics_path = art_dir / "metrics.json"
        if metrics_path.exists():
            with open(metrics_path, "r", encoding="utf-8") as f:
                self.metrics = json.load(f)

        # 8. Convergence history
        conv_path = art_dir / "convergence.json"
        if conv_path.exists():
            with open(conv_path, "r", encoding="utf-8") as f:
                self.convergence = json.load(f)

        self.is_loaded = True
        return self

    def fold_in_profile(
        self, profile_id: str, ratings_dict: Dict[int, float]
    ) -> Tuple[float, np.ndarray]:
        """Execute closed-form Ridge regression online fold-in for a profile in <50ms.
        
        Args:
            profile_id: Identifier of the user profile.
            ratings_dict: Mapping of item_idx -> rating value.
            
        Returns:
            Tuple of (b_u, p_u) representing the user bias and latent factor vector.
        """
        if self.funk_svd is None:
            raise RuntimeError("FunkSVD model is not loaded in registry")

        b_u, p_u = self.funk_svd.fold_in(ratings_dict)
        self._user_vectors[profile_id] = (b_u, p_u)
        return b_u, p_u

    def get_user_vector(
        self, profile_id: str, ratings_dict: Optional[Dict[int, float]] = None
    ) -> Tuple[float, np.ndarray]:
        """Retrieve or compute user latent factor vector."""
        if profile_id in self._user_vectors:
            return self._user_vectors[profile_id]

        if ratings_dict and len(ratings_dict) > 0:
            return self.fold_in_profile(profile_id, ratings_dict)

        if self.funk_svd is None:
            return 0.0, np.zeros(32, dtype=np.float32)

        return 0.0, np.zeros(self.funk_svd.n_factors, dtype=np.float32)

    def build_user_csr(self, ratings_dict: Dict[int, float]) -> sp.csr_matrix:
        """Construct a 1 x n_items sparse CSR matrix for user ratings."""
        n_items = self.funk_svd.n_items if self.funk_svd else 3706
        if not ratings_dict:
            return sp.csr_matrix((1, n_items), dtype=np.float32)

        items = []
        vals = []
        for item_idx, r in ratings_dict.items():
            if 0 <= item_idx < n_items:
                items.append(item_idx)
                vals.append(float(r))

        if not items:
            return sp.csr_matrix((1, n_items), dtype=np.float32)

        return sp.csr_matrix(
            (vals, ([0] * len(items), items)),
            shape=(1, n_items),
            dtype=np.float32,
        )

    def invalidate_user_vector(self, profile_id: str) -> None:
        """Evict cached latent vector for a profile."""
        self._user_vectors.pop(profile_id, None)


# Global registry instance
_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Dependency / accessor returning the initialized model registry singleton."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
        _registry.load_all()
    elif not _registry.is_loaded:
        _registry.load_all()
    return _registry
