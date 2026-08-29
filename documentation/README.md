# 🛵 Zomato End-to-End Business Intelligence & Machine Learning Platform

![Python] (https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL] (https://img.shields.io/badge/SQL-PostgreSQL%2FSQLite-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![PowerBI] (https://img.shields.io/badge/Power_BI-Desktop-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![Scikit-Learn] (https://img.shields.io/badge/scikit_learn-ML_Pipeline-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)

An enterprise-grade Data Engineering, Business Intelligence, and Predictive Analytics platform built on operational Zomato delivery data across 12 relational datasets.

---

## 📌 Repository Architecture

```text
Zomato_Business_Intelligence_Project/
├── data/
│   ├── raw/                        # 12 original CSV operational exports
│   └── cleaned/                    # Cleaned CSVs & Analytical Base Table (ABT)
├── sql/
│   ├── schema.sql                  # DDL scripts with Primary & Foreign Keys (3NF)
│   └── business_queries.sql        # SQL analytical views & KPIs
├── notebooks/
│   ├── 01_Data_Exploration.ipynb  # Initial profiling & FK audit
│   ├── 01_data_cleaning.ipynb      # Interactive cleaning pipeline development
│   ├── 02_eda.ipynb                # Exploratory Data Analysis & visual insights
│   ├── 03_feature_engineering.ipynb# Feature construction & ABT generation
│   ├── 04_delivery_time_model.ipynb# Delivery time regression experiments
│   └── 05_churn_model.ipynb       # Customer churn classification experiments
├── src/
│   ├── ingest.py                   # Data loading utilities
│   ├── clean.py                    # Automated data cleaning script
│   ├── features.py                 # Feature engineering script
│   ├── model_delivery.py           # Delivery time model training script
│   └── model_churn.py              # Churn classifier model training script
├── models/
│   ├── delivery_time_best_model.pkl# Serialized delivery time regression artifact
│   └── churn_best_model.pkl        # Serialized customer churn model artifact
├── reports/
│   ├── eda_report.pdf              # Generated EDA summary report
│   └── business_insights_report.pdf# Executive BI report
├── powerbi/
│   └── zomato_dashboard.pbix       # Interactive Power BI Dashboard
├── images/                         # Exported visual charts for README & reports
├── documentation/
│   ├── prd.docx                    # Product Requirements Document
│   └── data_quality_issues.md      # Raw data audit log & issue tracking
├── README.md
└── requirements.txt