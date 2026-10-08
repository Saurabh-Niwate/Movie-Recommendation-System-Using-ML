"""Download and extract MovieLens 1M dataset."""
import io
import zipfile
import requests
from pathlib import Path
from recsys.config import ML1M_URL, RAW_DIR


def download_ml_1m(dest_dir: Path = RAW_DIR, force: bool = False) -> Path:
    """Download ml-1m.zip from GroupLens and extract ratings.dat, movies.dat, users.dat."""
    expected_files = [dest_dir / "ratings.dat", dest_dir / "movies.dat", dest_dir / "users.dat"]
    if not force and all(f.exists() and f.stat().st_size > 0 for f in expected_files):
        print(f"[recsys] MovieLens 1M files already present in {dest_dir}")
        return dest_dir

    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"[recsys] Downloading MovieLens 1M from {ML1M_URL}...")
    response = requests.get(ML1M_URL, timeout=60)
    response.raise_for_status()

    print("[recsys] Extracting files...")
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        for member in zf.namelist():
            filename = Path(member).name
            if filename in ("ratings.dat", "movies.dat", "users.dat"):
                target_path = dest_dir / filename
                with zf.open(member) as src, open(target_path, "wb") as dst:
                    dst.write(src.read())
                print(f"[recsys] Extracted {filename} ({target_path.stat().st_size:,} bytes)")

    return dest_dir


if __name__ == "__main__":
    download_ml_1m()
