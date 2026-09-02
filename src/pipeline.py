# src/pipeline.py
from clean import clean_all_data
from features import build_features
from model_delivery import train_delivery_model
from model_churn import train_churn_model
from ingest import load_all_raw_datasets

def main():
    print("Starting Zomato BI Pipeline...")
    raw_data = load_all_raw_datasets()
    print(f"Loaded {len(raw_data)} raw datasets.")
    cleaned_data = clean_all_data(raw_data)
    print("Data cleaning completed successfully!")
    #build_features(cleaned_data)
    #train_delivery_model()
    #train_churn_model()
    print("Pipeline execution complete!")

if __name__ == "__main__":
    main()