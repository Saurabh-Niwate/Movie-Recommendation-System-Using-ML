"""Sparse matrix utilities."""
import numpy as np
import pandas as pd
import scipy.sparse as sp


def to_csr_matrix(df: pd.DataFrame, n_users: int, n_items: int) -> sp.csr_matrix:
    """Construct a CSR matrix of shape (n_users, n_items) from DataFrame with user_idx, item_idx, rating."""
    rows = df["user_idx"].to_numpy(dtype=np.int32)
    cols = df["item_idx"].to_numpy(dtype=np.int32)
    data = df["rating"].to_numpy(dtype=np.float32)

    return sp.csr_matrix((data, (rows, cols)), shape=(n_users, n_items), dtype=np.float32)


def to_binary_csr_matrix(df: pd.DataFrame, n_users: int, n_items: int) -> sp.csr_matrix:
    """Construct a binary CSR matrix indicating whether user rated item."""
    rows = df["user_idx"].to_numpy(dtype=np.int32)
    cols = df["item_idx"].to_numpy(dtype=np.int32)
    data = np.ones(len(df), dtype=np.float32)

    return sp.csr_matrix((data, (rows, cols)), shape=(n_users, n_items), dtype=np.float32)
