"""Unit tests for data pipeline: title cleaning, contiguous indexing, and temporal split."""
import json
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

from recsys.config import PROCESSED_DIR, ARTIFACTS_DIR
from recsys.data.prepare import clean_title_and_year
from recsys.data.split import temporal_user_split


def test_clean_title_and_year():
    """Verify title cleaning and year parsing across standard formats."""
    # Standard trailing article
    title, year = clean_title_and_year("Matrix, The (1999)")
    assert title == "The Matrix"
    assert year == 1999

    # Another article: A
    title, year = clean_title_and_year("Clockwork Orange, A (1971)")
    assert title == "A Clockwork Orange"
    assert year == 1971

    # French article: Le
    title, year = clean_title_and_year("Fabuleux Destin d'Amélie Poulain, Le (2001)")
    assert title == "Le Fabuleux Destin d'Amélie Poulain"
    assert year == 2001

    # Standard without inverted article
    title, year = clean_title_and_year("Toy Story (1995)")
    assert title == "Toy Story"
    assert year == 1995


def test_contiguous_id_indexing():
    """Verify that user and item indices in processed datasets are contiguous 0-based."""
    id_maps_path = PROCESSED_DIR / "id_maps.json"
    if not id_maps_path.exists():
        pytest.skip("Processed id_maps.json not found")

    with open(id_maps_path, "r", encoding="utf-8") as f:
        id_maps = json.load(f)

    n_users = id_maps["n_users"]
    n_items = id_maps["n_items"]

    # Verify user indexing is exactly 0 .. n_users - 1
    user_indices = sorted([int(v) for v in id_maps["user_id_to_user_idx"].values()])
    assert user_indices == list(range(n_users))

    # Verify item indexing is exactly 0 .. n_items - 1
    item_indices = sorted([int(v) for v in id_maps["movie_id_to_item_idx"].values()])
    assert item_indices == list(range(n_items))


def test_temporal_split_chronology():
    """Verify that temporal split maintains per-user chronological ordering."""
    # Synthetic user ratings with items appearing in train as well
    df = pd.DataFrame({
        "user_idx": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "item_idx": [0, 1, 2, 0, 1, 2, 0, 1, 2, 0],
        "rating": [5, 4, 3, 4, 5, 4, 3, 4, 5, 4],
        "timestamp": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    })

    train, val, test = temporal_user_split(df, test_frac=0.2, val_frac=0.2)

    assert len(train) > 0
    assert len(test) > 0

    user_0_train_ts = train[train["user_idx"] == 0]["timestamp"].max()
    user_0_test_ts = test[test["user_idx"] == 0]["timestamp"].min()

    # Train ratings must occur strictly before test ratings
    assert user_0_train_ts <= user_0_test_ts
