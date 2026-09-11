# 🛵 Zomato End-to-End Business Intelligence & Machine Learning Platform

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-PostgreSQL%2FSQLite-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![PowerBI](https://img.shields.io/badge/Power_BI-Desktop-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![Scikit-Learn](https://img.shields.io/badge/scikit_learn-ML_Pipeline-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)

An end-to-end data analytics and business intelligence pipeline built on a 12-dataset relational food delivery ecosystem. This project transforms normalized data into actionable executive insights, featuring an interactive EDA notebook suite with **30+ publication-grade visualizations** adhering to Zomato's brand identity. An enterprise-grade Data Engineering, Business Intelligence, and Predictive Analytics platform built on operational Zomato delivery data across 12 relational datasets.
---

## 📌 Project Overview

This repository houses the full analytical pipeline for analyzing customer behavior, revenue performance, delivery logistics, and operational bottlenecks across a food delivery network.

* **Database Architecture:** 12 relational datasets normalized to 3NF.
* **Storage & Ingestion:** Optimized `.parquet` data files for high-throughput I/O.
* **Visual Standards:** Custom Matplotlib and Seaborn theme engine aligned with Zomato brand guidelines (Zomato Red `#E23744`, Dark Red `#CB202D`, Charcoal `#2D2D2D`, and clean neutral backdrops `#F8F9FA`).
* **Analytical Scope:** 8 core business domain questions explored through 30+ non-redundant statistical charts.
--- 

## 🗂️ Data Architecture (12 Datasets)

The pipeline processes and joins 12 cleaned datasets (`*_cleaned.parquet`):

| Dataset | Primary Key / Identifier | Core Description |
| :--- | :--- | :--- |
| `orders` | `OrderID` | Core transactional log containing order values, timestamps, status, and delivery durations. |
| `customers` | `CustomerID` | Demographics, registration dates, city locations, and preferred cuisines. |
| `restaurants` | `RestaurantID` | Cuisine types, average costs for two, city locations, and rating profiles. |
| `delivery_partners` | `DeliveryPartnerID` | Vehicle types, experience (`CompletedDeliveries`), and partner ratings. |
| `menu` | `MenuItemID` | Item categories, preparation times, prices, and dietary flags (`IsVegetarian`). |
| `cities` | `CityID` | Population metrics, income tiers, and geographic classification. |
| `customer_feedback` | `FeedbackID` | Multidimensional feedback (Food, Delivery, Overall ratings, Complaints). |
| `order_items` | `OrderItemID` | Transaction line-item granularity linking orders to specific menu items. |
| `payments` | `PaymentID` | Payment gateway types, transaction status, and timestamps. |
| `promotions` | `PromotionID` | Active discount campaign parameters and usage metrics. |
| `traffic` | `TrafficLogID` | Congestion levels, average partner speeds, and routing delay metrics. |
| `weather` | `WeatherLogID` | Meteorological logs (temperature, precipitation, weather conditions). |
---

## 📊 Exploratory Data Analysis (EDA) Core Business Questions

The EDA notebook (`notebooks/02_eda.ipynb`) and automated export script (`src/generate_all_eda.py`) systematically address 8 primary business domains:

1. **Top Revenue Generators:** Longitudinal revenue tracking across top restaurants and cuisines over quarters/months.
2. **Peak Ordering Dynamics:** Hourly order demand curves across 24-hour cycles, contrasting weekday vs. weekend patterns.
3. **Delivery & Logistics Variance:** Delivery duration distributions (`DeliveryTimeMinutes`) analyzed across cities, traffic congestion levels, and weather events (with 99th percentile IQR outlier capping).
4. **Basket Economics:** Average order value (AOV) and basket sizes segmented by customer membership tiers.
5. **Customer Retention & Churn:** Analysis of one-time vs. repeat customer proportions and lifecycle distribution.
6. **Partner Performance Logistics:** Efficiency metrics comparing delivery vehicle types, partner ratings, and speed profiles.
7. **Order Friction & Cancellations:** Root cause classification of cancelled/refunded orders and operational bottlenecks.
8. **Customer Lifetime Value (CLV):** Geographic and cuisine-level CLV distribution across tier 1–3 cities.---

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

```
--- 

