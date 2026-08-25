# src/pipeline.py
from clean import clean_all_data
from features import build_features
from model_delivery import train_delivery_model
from model_churn import train_churn_model

def main():
    print("Starting Zomato BI Pipeline...")
    clean_all_data()
    build_features()
    train_delivery_model()
    train_churn_model()
    print("Pipeline execution complete!")

if __name__ == "__main__":
    main()