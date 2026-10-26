# Zomato Business Intelligence & Delivery Analytics

Internship project (Internmo) built on 12 linked food-delivery datasets: orders, customers, restaurants, delivery partners, payments, promotions, feedback, menu, order items, cities, weather and traffic. The goal was to take messy operational exports and turn them into something the operations, partnerships and marketing teams could actually use: a clean database, SQL reporting, two predictive models and a Power BI dashboard.

Tools: Python (pandas, scikit-learn), PostgreSQL, Power BI Desktop, Matplotlib/Seaborn.

## What's in here

```text
Zomato_BI_Project/
├── data/
│   ├── raw/            # 12 original CSV exports
│   ├── cleaned/        # cleaned tables (CSV + parquet)
│   └── processed/      # features, model outputs, restaurant scores
├── notebooks/          # 00–06: understanding the data → cleaning → EDA → features → models
├── src/                # the same steps as scripts, run end to end by pipeline.py
├── sql/
│   ├── schema.sql              # 3NF schema with primary/foreign keys
│   └── business_queries.sql    # 32 business queries, incl. views, a procedure and a trigger
├── models/             # saved delivery-time and churn models (.pkl)
├── powerbi/            # zomato_dashboard.pbix (6 pages) + theme
├── reports/            # Zomato_Business_Insights_Report.docx
├── documentation/      # data_quality_issues.md (cleaning audit)
└── images/             # ER diagram
```

## Running it

```bash
pip install -r requirements.txt
python src/pipeline.py
```

This loads the raw files, cleans them, builds features, trains both models and writes the table the dashboard needs (`data/processed/restaurant_scores.csv`). To use the database side, run `sql/schema.sql` in PostgreSQL 14+, load the cleaned CSVs, then run the queries in `business_queries.sql`.

## Data cleaning

The raw data had duplicate orders, orders pointing to customers that didn't exist, negative ages, broken phone numbers and city names spelled several different ways. All 9 known issues from the PRD were fixed, and only 613 of 178,077 rows (0.34%) were dropped, each for a documented reason. The full audit, table by table, is in `documentation/data_quality_issues.md`.

## Main findings

- About a third of orders fail: 22.3% are cancelled and 11.5% end as "Food Not Delivered". That's ₹27.1 lakh lost, compared with ₹53.1 lakh delivered over 2023–24.
- The bottom-10 restaurants in each city cancel 28.5% of orders, against 16% for the top 10. The composite score (40% rating, 30% cancellations, 30% late deliveries) ranks all 1,200 restaurants within their own city.
- Delivery time hardly changes with weather, traffic or peak hours (each makes less than a minute of difference). Ludhiana and Nagpur have the most late deliveries, at around 18%.
- 38% of customers only ever ordered once, and 87% hadn't ordered in the last 60 days.
- Orders peak at 12–1 pm and 7–8 pm. Weekdays and weekends look about the same.

The full write-up with recommendations is in `reports/Zomato_Business_Insights_Report.docx`.

## Models

| Model | Best result | Baseline | PRD target |
| --- | --- | --- | --- |
| Delivery time (regression, 7 models tried) | RMSE 14.9 min, R² ≈ 0 | RMSE 14.9 min | R² ≥ 0.75, RMSE ≤ 6 |
| Churn in 60 days (classification, 5 models tried) | F1 0.83, ROC-AUC 0.54 | F1 0.93 (predict everyone churns) | F1 ≥ 0.70 |

Neither model beats its simple baseline, so they don't hit the targets. The data doesn't include the things that probably drive these outcomes: promised delivery time, kitchen wait time, partner location at assignment and cancellation reasons. The feature importances are still useful. Partner delivery efficiency, food cost, order hour and prep time matter most for delivery time, while weather and traffic barely register.

## Dashboard

`powerbi/zomato_dashboard.pbix` has six pages built from the cleaned and processed CSVs, following PRD Section 25. If the project folder moves, update the `DataFolder` parameter in Power Query and refresh.

## Known limitations

- "Late" comes from the order status, because the data has no promised delivery time.
- Weather and traffic are daily city-level averages, not the conditions at the moment each order was placed.
- A few restaurant ratings were filled in with the city median before scoring.
