import os
import pandas as pd

RAW_DATA_DIR = os.path.join("data", "raw")
CLEAN_DATA_DIR = os.path.join("data", "cleaned")

def load_raw_dataset(filename: str) -> pd.DataFrame:
    """Loads a single raw CSV file from data/raw/."""
    file_path = os.path.join(RAW_DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_csv(file_path, dtype=str)  # Load as string initially to preserve raw formats

def load_all_raw_datasets() -> dict[str, pd.DataFrame]:
    """Loads all 12 raw CSV datasets into a dictionary of DataFrames."""
    datasets = {}
    files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith('.csv')]
    for file in files:
        key = file.replace('.csv', '')
        datasets[key] = load_raw_dataset(file)
        print(f"Loaded {file} ({len(datasets[key])} rows)")
    return datasets

if __name__ == "__main__":
    data = load_all_raw_datasets()