# src/pipeline.py
from clean import clean_all_data
from features import build_features, export_featured_datasets
from model_delivery import train_delivery_model
from model_churn import train_churn_model
from ingest import BASE_DIR, load_all_raw_datasets

def main():
    print("Starting Zomato BI Pipeline...")
    raw_data = load_all_raw_datasets()
    print(f"Loaded {len(raw_data)} raw datasets.")
    cleaned_data = clean_all_data(raw_data)
    print("Data cleaning completed successfully!")
    # Churn model reads featured_orders.parquet, which is gitignored, so rebuild it first
    df_features = build_features()
    export_featured_datasets(df_features, base_dir=str(BASE_DIR / "data" / "processed"))
    train_delivery_model()
    train_churn_model()
    print("Pipeline execution complete!")

if __name__ == "__main__":
    main()