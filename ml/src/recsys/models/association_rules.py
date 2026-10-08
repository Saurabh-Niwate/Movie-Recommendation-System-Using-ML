"""Association rules recommender computing co-occurrence Lift for 'Users also watched'."""
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
import scipy.sparse as sp


class AssociationRules:
    """Computes co-occurrence matrix and Lift metric for items."""

    name: str = "association_rules"

    def __init__(
        self,
        min_cooccurrence: int = 10,
        top_k: int = 20,
    ):
        self.min_cooccurrence = min_cooccurrence
        self.top_k = top_k
        self.n_users: int = 0
        self.n_items: int = 0
        self.item_counts: np.ndarray = np.array([], dtype=np.int32)
        self.rules: Dict[int, List[Dict[str, Any]]] = {}

    def fit(self, R: sp.csr_matrix) -> "AssociationRules":
        """Compute co-occurrence matrix and Lift across all item pairs.
        
        Args:
            R: User-item rating CSR matrix (n_users x n_items).
        """
        R = R.tocsr()
        self.n_users, self.n_items = R.shape

        # Binary interaction matrix B
        B = R.copy()
        B.data[:] = 1.0

        # Item support counts: c_i = sum_u B_{ui}
        B_csc = B.tocsc()
        self.item_counts = np.diff(B_csc.indptr).astype(np.int32)

        # Co-occurrence matrix: C = B.T @ B
        C = (B.T @ B).tocsr()

        N = float(self.n_users)
        self.rules = {}

        # Precompute top-k associations for each item
        for i in range(self.n_items):
            c_i = self.item_counts[i]
            if c_i == 0:
                self.rules[i] = []
                continue

            row_start = C.indptr[i]
            row_end = C.indptr[i + 1]
            candidate_indices = C.indices[row_start:row_end]
            candidate_counts = C.data[row_start:row_end].astype(np.float32)

            # Exclude self
            mask = candidate_indices != i
            candidate_indices = candidate_indices[mask]
            candidate_counts = candidate_counts[mask]

            if len(candidate_indices) == 0:
                self.rules[i] = []
                continue

            # Filter by min_cooccurrence if possible
            cooc_mask = candidate_counts >= self.min_cooccurrence
            if np.any(cooc_mask):
                cand_idx = candidate_indices[cooc_mask]
                cand_cooc = candidate_counts[cooc_mask]
            else:
                # Fallback to top co-occurring items if threshold is too strict
                cand_idx = candidate_indices
                cand_cooc = candidate_counts

            c_j = self.item_counts[cand_idx].astype(np.float32)
            # Lift(i, j) = (C_{ij} * N) / (c_i * c_j)
            lift_values = (cand_cooc * N) / (float(c_i) * c_j + 1e-9)

            # Sort descending by Lift, tiebreak by cooccurrence
            order = np.lexsort((-cand_cooc, -lift_values))
            cand_idx = cand_idx[order][:self.top_k]
            cand_lift = lift_values[order][:self.top_k]
            cand_cooc = cand_cooc[order][:self.top_k]

            item_rules = [
                {
                    "item_idx": int(idx),
                    "lift": round(float(lift), 4),
                    "cooccurrence": int(cooc),
                }
                for idx, lift, cooc in zip(cand_idx, cand_lift, cand_cooc)
            ]
            self.rules[i] = item_rules

        return self

    def get_also_watched(
        self,
        item_idx: int,
        k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Return top-k 'Users also watched' items for a given item index."""
        if item_idx not in self.rules:
            return []
        return self.rules[item_idx][:k]

    def save(self, path: Path) -> None:
        """Save rules to JSON and Parquet."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        json_path = path if path.suffix == ".json" else path.with_suffix(".json")
        parquet_path = path if path.suffix == ".parquet" else path.with_suffix(".parquet")

        # 1. Save JSON representation
        serializable_rules = {str(k): v for k, v in self.rules.items()}
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(serializable_rules, f, indent=2)

        # 2. Save Parquet representation
        rows = []
        for i, associations in self.rules.items():
            for assoc in associations:
                rows.append({
                    "item_idx": int(i),
                    "related_item_idx": int(assoc["item_idx"]),
                    "lift": float(assoc["lift"]),
                    "cooccurrence": int(assoc["cooccurrence"]),
                })
        if rows:
            df = pd.DataFrame(rows)
            df.to_parquet(parquet_path, index=False)

    @classmethod
    def load(cls, path: Path) -> "AssociationRules":
        """Load AssociationRules from JSON or Parquet."""
        path = Path(path)
        json_path = path if path.suffix == ".json" else path.with_suffix(".json")
        parquet_path = path if path.suffix == ".parquet" else path.with_suffix(".parquet")

        model = cls()
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                raw_rules = json.load(f)
            model.rules = {int(k): v for k, v in raw_rules.items()}
            model.n_items = len(model.rules)
        elif parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            rules: Dict[int, List[Dict[str, Any]]] = {}
            for _, row in df.iterrows():
                i = int(row["item_idx"])
                if i not in rules:
                    rules[i] = []
                rules[i].append({
                    "item_idx": int(row["related_item_idx"]),
                    "lift": float(row["lift"]),
                    "cooccurrence": int(row["cooccurrence"]),
                })
            model.rules = rules
            model.n_items = len(model.rules)
        return model
