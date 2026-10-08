"""Typer CLI interface for recsys package."""
import json
import time
from pathlib import Path
from typing import List, Optional
import typer
import pandas as pd
import scipy.sparse as sp

from recsys.config import (
    PROCESSED_DIR,
    ARTIFACTS_DIR,
    RAW_DIR,
)
from recsys.data.download import download_ml_1m
from recsys.data.prepare import prepare_dataset
from recsys.data.split import temporal_user_split, save_splits
from recsys.data.matrix import to_csr_matrix
from recsys.models.popularity import PopularityRecommender
from recsys.models.item_knn import ItemKNN
from recsys.models.funk_svd import FunkSVD
from recsys.models.association_rules import AssociationRules
from recsys.profiles.cluster import export_profiles
from recsys.eval.evaluate import evaluate_model

app = typer.Typer(help="Movie Recommendation System ML CLI")


def _get_id_maps() -> dict:
    """Load or copy id_maps.json from processed or artifacts directory."""
    artifacts_path = ARTIFACTS_DIR / "id_maps.json"
    processed_path = PROCESSED_DIR / "id_maps.json"

    if artifacts_path.exists():
        with open(artifacts_path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif processed_path.exists():
        with open(processed_path, "r", encoding="utf-8") as f:
            id_maps = json.load(f)
        id_maps["movie2idx"] = id_maps.get("movie_id_to_item_idx", {})
        id_maps["idx2movie"] = id_maps.get("item_idx_to_movie_id", {})
        id_maps["user2idx"] = id_maps.get("user_id_to_user_idx", {})
        id_maps["idx2user"] = id_maps.get("user_idx_to_user_id", {})
        with open(artifacts_path, "w", encoding="utf-8") as f:
            json.dump(id_maps, f)
        return id_maps
    else:
        raise FileNotFoundError("id_maps.json not found in processed or artifacts directory")


@app.command()
def download(force: bool = typer.Option(False, "--force", "-f", help="Force re-download")):
    """Download MovieLens 1M dataset."""
    download_ml_1m(force=force)


@app.command()
def prepare():
    """Prepare raw data, create contiguous ID mappings, and generate temporal splits."""
    ratings, movies, users = prepare_dataset()
    train, val, test = temporal_user_split(ratings)
    save_splits(train, val, test)
    export_profiles()


@app.command()
def train(
    model_name: str = typer.Option("all", "--model", "-m", help="popularity, item_knn, funk_svd, association_rules, or all"),
    k: int = typer.Option(40, "--k", help="KNN neighborhood size"),
    shrink: float = typer.Option(50.0, "--shrink", help="Significance shrinkage parameter"),
    n_factors: int = typer.Option(32, "--factors", help="Funk-SVD latent factors"),
    epochs: int = typer.Option(15, "--epochs", help="Funk-SVD SGD epochs"),
    lr: float = typer.Option(0.008, "--lr", help="Funk-SVD learning rate"),
    reg_bias: float = typer.Option(0.02, "--reg-bias", help="Funk-SVD bias regularization"),
    reg_factor: float = typer.Option(0.05, "--reg-factor", help="Funk-SVD factor regularization"),
):
    """Train recommendation model(s) and save artifacts."""
    train_df = pd.read_parquet(PROCESSED_DIR / "train.parquet")
    id_maps = _get_id_maps()

    n_users = id_maps["n_users"]
    n_items = id_maps["n_items"]
    train_R = to_csr_matrix(train_df, n_users, n_items)

    val_R = None
    val_path = PROCESSED_DIR / "val.parquet"
    if val_path.exists():
        val_df = pd.read_parquet(val_path)
        val_R = to_csr_matrix(val_df, n_users, n_items)

    if model_name.lower() == "all":
        models_to_train = ["popularity", "item_knn", "funk_svd", "association_rules"]
    else:
        models_to_train = [m.strip().lower() for m in model_name.split(",")]

    for name in models_to_train:
        t0 = time.time()
        if name == "popularity":
            print(f"[recsys] Training PopularityRecommender...")
            pop = PopularityRecommender().fit(train_R)
            pop.save(ARTIFACTS_DIR / "popularity.json")
            print(f"[recsys] Saved popularity.json in {time.time() - t0:.2f}s")

        elif name == "item_knn":
            print(f"[recsys] Training ItemKNN (k={k}, shrink={shrink})...")
            knn = ItemKNN(k=k, shrink=shrink).fit(train_R)
            knn.save(ARTIFACTS_DIR / "item_knn.npz")
            print(f"[recsys] Saved item_knn.npz in {time.time() - t0:.2f}s")

        elif name == "funk_svd":
            print(f"[recsys] Training FunkSVD (factors={n_factors}, epochs={epochs}, lr={lr}, reg_b={reg_bias}, reg_f={reg_factor})...")
            svd = FunkSVD(n_factors=n_factors, lr=lr, reg_bias=reg_bias, reg_factor=reg_factor, n_epochs=epochs).fit(train_R, val_R=val_R)
            svd.save(ARTIFACTS_DIR / "funk_svd.npz")
            print(f"[recsys] Saved funk_svd.npz in {time.time() - t0:.2f}s")

        elif name in ("association_rules", "associations"):
            print(f"[recsys] Training AssociationRules...")
            assoc = AssociationRules().fit(train_R)
            assoc.save(ARTIFACTS_DIR / "associations.parquet")
            print(f"[recsys] Saved associations.parquet & associations.json in {time.time() - t0:.2f}s")

        else:
            typer.echo(f"Unknown model: {name}", err=True)

    # Always ensure profiles.json exists
    if not (ARTIFACTS_DIR / "profiles.json").exists() or model_name.lower() == "all":
        export_profiles()


@app.command()
def evaluate(
    models: str = typer.Option("popularity,item_knn,funk_svd", "--models", help="Comma-separated model names"),
    k: int = typer.Option(10, "--k", help="Ranking cutoff"),
):
    """Evaluate trained model(s) against the temporal test set."""
    train_df = pd.read_parquet(PROCESSED_DIR / "train.parquet")
    test_df = pd.read_parquet(PROCESSED_DIR / "test.parquet")
    id_maps = _get_id_maps()

    n_users = id_maps["n_users"]
    n_items = id_maps["n_items"]
    train_R = to_csr_matrix(train_df, n_users, n_items)

    model_names = [m.strip().lower() for m in models.split(",")]
    metrics_report = {
        "split": "temporal_80_20",
        "k": k,
        "n_users": n_users,
        "n_items": n_items,
        "test_ratings_count": len(test_df),
        "models": {},
    }

    # Load existing metrics if available
    metrics_file = ARTIFACTS_DIR / "metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
                if "models" in existing and isinstance(existing["models"], dict):
                    metrics_report["models"] = existing["models"]
                for key in ["popularity", "item_knn", "funk_svd"]:
                    if key in existing:
                        metrics_report[key] = existing[key]
        except Exception:
            pass

    for name in model_names:
        if name == "popularity":
            model = PopularityRecommender.load(ARTIFACTS_DIR / "popularity.json")
        elif name == "item_knn":
            model = ItemKNN.load(ARTIFACTS_DIR / "item_knn.npz")
        elif name == "funk_svd":
            model = FunkSVD.load(ARTIFACTS_DIR / "funk_svd.npz")
        else:
            typer.echo(f"Unknown model name: {name}", err=True)
            continue

        res = evaluate_model(model, train_R, test_df, k=k)
        metrics_report["models"][name] = res
        metrics_report[name] = res

    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics_report, f, indent=2)
    print(f"[recsys] Saved evaluation report to {metrics_file}")


@app.command("train-all")
def train_all():
    """Run end-to-end pipeline: download -> prepare -> train -> evaluate."""
    download(force=False)
    prepare()
    train(model_name="all")
    evaluate(models="popularity,item_knn,funk_svd")


if __name__ == "__main__":
    app()
