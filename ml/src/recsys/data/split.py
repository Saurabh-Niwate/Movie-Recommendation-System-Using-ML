"""Dataset splitting: temporal per-user 80/20 train/test split and validation split."""
from pathlib import Path
from typing import Tuple
import numpy as np
import pandas as pd
from recsys.config import PROCESSED_DIR, TEST_FRACTION, VAL_FRACTION


def temporal_user_split(
    df: pd.DataFrame,
    test_frac: float = TEST_FRACTION,
    val_frac: float = VAL_FRACTION,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Perform temporal per-user split.
    
    1. Sort per-user ratings by timestamp chronologically.
    2. Split per-user into:
       - train: oldest (1 - test_frac)
       - test: newest test_frac
    3. Further split train into:
       - train_split: oldest (1 - val_frac)
       - val_split: newest val_frac
    4. Filter out cold items in test/val that never appeared in train_split.
    """
    print("[recsys] Performing temporal per-user split...")
    df_sorted = df.sort_values(["user_idx", "timestamp"], kind="stable").reset_index(drop=True)

    # Rank within each user
    cumcount = df_sorted.groupby("user_idx").cumcount()
    user_counts = df_sorted.groupby("user_idx")["user_idx"].transform("count")

    # Threshold for test
    test_thresh = np.floor(user_counts * (1.0 - test_frac)).astype(int)
    is_test = cumcount >= test_thresh

    train_val_df = df_sorted[~is_test].copy()
    test_df = df_sorted[is_test].copy()

    # Threshold for val within train_val
    tv_counts = train_val_df.groupby("user_idx")["user_idx"].transform("count")
    val_thresh = np.floor(tv_counts * (1.0 - val_frac)).astype(int)
    tv_cumcount = train_val_df.groupby("user_idx").cumcount()
    is_val = tv_cumcount >= val_thresh

    train_df = train_val_df[~is_val].copy()
    val_df = train_val_df[is_val].copy()

    # Cold item check
    train_items = set(train_df["item_idx"].unique())
    initial_val_len = len(val_df)
    val_df = val_df[val_df["item_idx"].isin(train_items)].copy()
    if len(val_df) < initial_val_len:
        print(f"[recsys] Filtered {initial_val_len - len(val_df)} cold items from val set.")

    initial_test_len = len(test_df)
    test_df = test_df[test_df["item_idx"].isin(train_items)].copy()
    if len(test_df) < initial_test_len:
        print(f"[recsys] Filtered {initial_test_len - len(test_df)} cold items from test set.")

    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    print(
        f"[recsys] Split complete:\n"
        f"  - Train: {len(train_df):,} ratings ({len(train_df)/len(df):.1%})\n"
        f"  - Val:   {len(val_df):,} ratings ({len(val_df)/len(df):.1%})\n"
        f"  - Test:  {len(test_df):,} ratings ({len(test_df)/len(df):.1%})"
    )
    return train_df, val_df, test_df


def save_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: Path = PROCESSED_DIR,
) -> None:
    """Save split DataFrames to Parquet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    train_df.to_parquet(output_dir / "train.parquet", index=False)
    val_df.to_parquet(output_dir / "val.parquet", index=False)
    test_df.to_parquet(output_dir / "test.parquet", index=False)
    print(f"[recsys] Saved splits to {output_dir}")


if __name__ == "__main__":
    ratings = pd.read_parquet(PROCESSED_DIR / "ratings.parquet")
    train, val, test = temporal_user_split(ratings)
    save_splits(train, val, test)
