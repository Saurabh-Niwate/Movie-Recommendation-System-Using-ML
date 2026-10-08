"""Configuration and path definitions for the recsys package."""
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parents[3]  # ML project root
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "ml-1m"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"
ARTIFACTS_DIR = ROOT / "artifacts" / "v1"

# Dataset URL
ML1M_URL = "https://files.grouplens.org/datasets/movielens/ml-1m.zip"

# Evaluation & Modeling Constants
RELEVANCE_THRESHOLD = 4.0  # rating >= 4 counts as relevant
TEST_FRACTION = 0.20
VAL_FRACTION = 0.10
SEED = 42

# Ensure required directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
