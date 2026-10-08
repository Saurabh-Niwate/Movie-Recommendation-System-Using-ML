import time
import pytest
import numpy as np
from app.infra.model_registry import get_model_registry, resolve_artifacts_dir


def test_artifacts_dir_resolution():
    art_dir = resolve_artifacts_dir()
    assert art_dir.is_dir()
    assert (art_dir / "funk_svd.npz").is_file()
    assert (art_dir / "item_knn.npz").is_file()
    assert (art_dir / "metrics.json").is_file()


def test_model_registry_loaded():
    reg = get_model_registry()
    assert reg.is_loaded is True
    assert reg.funk_svd is not None
    assert reg.item_knn is not None
    assert reg.associations is not None
    assert reg.popularity is not None
    assert len(reg.movie_id_to_item_idx) > 0
    assert len(reg.item_idx_to_movie_id) > 0


def test_model_registry_fold_in_speed_and_shape():
    reg = get_model_registry()
    ratings = {0: 4.5, 1: 3.0, 10: 5.0, 50: 2.0, 100: 4.0}

    t0 = time.perf_counter()
    b_u, p_u = reg.fold_in_profile("test_profile_speed", ratings)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert elapsed_ms < 50.0, f"Fold-in took {elapsed_ms:.2f}ms, expected < 50ms"
    assert isinstance(b_u, float)
    assert isinstance(p_u, np.ndarray)
    assert p_u.shape == (reg.funk_svd.n_factors,)


def test_model_registry_build_user_csr():
    reg = get_model_registry()
    ratings = {5: 4.0, 12: 3.5}
    csr = reg.build_user_csr(ratings)
    assert csr.shape == (1, reg.funk_svd.n_items)
    assert csr.nnz == 2
    assert csr[0, 5] == 4.0
    assert csr[0, 12] == 3.5
