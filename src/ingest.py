import os
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
CLEAN_DATA_DIR = BASE_DIR / "data" / "cleaned"

def load_raw_dataset(filename: str) -> pd.DataFrame:
    file_path = RAW_DATA_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_csv(file_path, dtype=str)

def load_all_raw_datasets() -> dict[str, pd.DataFrame]:
    datasets = {}
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Directory missing: {RAW_DATA_DIR}")
        
    for file_path in RAW_DATA_DIR.glob("*.csv"):
        key = file_path.stem
        datasets[key] = load_raw_dataset(file_path.name)
        
    return datasets

if __name__ == "__main__":
    data = load_all_raw_datasets()