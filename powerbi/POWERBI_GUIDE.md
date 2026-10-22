# Power BI Dashboard: Build Guide

Six-page dashboard for PRD Section 25, built in Power BI Desktop (Windows VM in UTM) from the project CSV files.
Save the finished file as `powerbi/zomato_dashboard.pbix`.

## 0. Before you start

1. On the Mac, run the pipeline so every CSV is up to date:
   ```bash
   python src/pipeline.py
   ```
2. Make the project folder visible in Windows. Either:
   - **Shared folder:** in UTM, open the VM settings → *Sharing* → choose the `Zomato_BI_Project` folder. With the SPICE guest tools installed in Windows, it shows up as a network drive. Refreshing then always reads the latest files.
   - **Copy:** copy `Zomato_BI_Project` into Windows (e.g. `C:\Zomato_BI_Project`). Re-copy the `data` folder after each pipeline run.

## 1. Data folder parameter (NFR-04: refresh without re-mapping)

*Home → Transform data → Manage Parameters → New*
- Name: `DataFolder`
- Type: Text
- Current value: the path to the project's `data` folder **with a trailing backslash**, e.g. `C:\Zomato_BI_Project\data\`

If the folder moves, change only this value.

## 2. Load the tables

For each row below: *Home → New Source → Blank Query → Advanced Editor*, paste the template, change the file path, then rename the query to the table name.

```m
let
    Source = Csv.Document(
        File.Contents(DataFolder & "cleaned\customers_cleaned.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true])
in
    Promoted
```

| Table name | File | Notes |
|---|---|---|
| `Orders` | `processed\featured_orders.csv` | Fact table: cleaned orders + engineered features. `City` = customer's city |
| `Customers` | `cleaned\customers_cleaned.csv` | |
| `Restaurants` | `cleaned\restaurants_cleaned.csv` | |
| `DeliveryPartners` | `cleaned\delivery_partners_cleaned.csv` | |
| `Cities` | `cleaned\cities_cleaned.csv` | |
| `Feedback` | `cleaned\customer_feedback_cleaned.csv` | |
| `RestaurantScores` | `processed\restaurant_scores.csv` | Composite score (same formula as `vw_restaurant_composite_score`) |
| `ChurnScores` | `processed\churn_scores.csv` | Churn probability, risk band, RFM segment |
| `ChurnDrivers` | `processed\churn_top_drivers.csv` | |
| `ChurnModels` | `processed\churn_model_comparison.csv` | |
| `DeliveryPredictions` | `processed\delivery_predictions.csv` | Test set: actual vs predicted |
| `DeliveryImportance` | `processed\delivery_feature_importance.csv` | |
| `DeliveryModels` | `processed\delivery_model_comparison.csv` | |

**Data types.** Select all columns → *Transform → Detect Data Type*, then check:
- `Orders[OrderDate]`: **Date**
- `Orders[FinalAmount]`, `Orders[Discount]`, `Orders[DeliveryTimeMinutes]`: Decimal / Whole number
- ID columns: Whole number

If decimals load wrong (e.g. `315.85` becomes `31585`), use *Change Type → Using Locale → English (United States)*.

*Close & Apply.*

## 3. Date table

*Modeling → New table:*

```dax
Date =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2023, 1, 1 ), DATE ( 2024, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Quarter", "Q" & QUARTER ( [Date] ),
    "Month", FORMAT ( [Date], "MMM yyyy" ),
    "MonthNumber", YEAR ( [Date] ) * 100 + MONTH ( [Date] ),
    "MonthStart", DATE ( YEAR ( [Date] ), MONTH ( [Date] ), 1 )
)
```

- Select `Date[Month]` → *Sort by column* → `MonthNumber`.
- *Table tools → Mark as date table* → `Date[Date]`.

## 4. Relationships

*Model view*. All are many-to-one (`*` → `1`) with single cross-filter direction. If Power BI creates a one-to-one for the ML tables, that's fine.

| From (many) | To (one) |
|---|---|
| `Orders[OrderDate]` | `Date[Date]` |
| `Orders[CustomerID]` | `Customers[CustomerID]` |
| `Orders[RestaurantID]` | `Restaurants[RestaurantID]` |
| `Orders[DeliveryPartnerID]` | `DeliveryPartners[DeliveryPartnerID]` |
| `Orders[City]` | `Cities[City]` |
| `Feedback[OrderID]` | `Orders[OrderID]` |
| `RestaurantScores[City]` | `Cities[City]` |
| `ChurnScores[CustomerID]` | `Customers[CustomerID]` |
| `DeliveryPredictions[OrderID]` | `Orders[OrderID]` |

Delete any other relationships Power BI auto-detects, especially `Customers[City]`, `Restaurants[City]` or `DeliveryPartners[City]` → `Cities`. They create ambiguous filter paths.

`ChurnDrivers`, `ChurnModels`, `DeliveryImportance` and `DeliveryModels` stay unrelated.

## 5. Calculated columns

```dax
-- Customers table
Lifetime Value =
CALCULATE (
    SUM ( Orders[FinalAmount] ),
    Orders[OrderStatus] IN { "Delivered", "Delivered Late" }
)
```

```dax
-- Orders table
Rain = IF ( Orders[RainImpact] = 1, "Rain", "No rain" )
```

## 6. Measures

Create an empty table to hold them (*Home → Enter data* → name it `_Measures`), then add each measure there.

**KPI definitions used everywhere**
- **Revenue:** `FinalAmount` of `Delivered` + `Delivered Late` orders
- **Late delivery:** status `Delivered Late`, as a share of delivered orders
- **Active customer:** placed an order in the 90 days up to the end of the selected period

```dax
Total Revenue =
CALCULATE ( SUM ( Orders[FinalAmount] ), Orders[OrderStatus] IN { "Delivered", "Delivered Late" } )

Total Orders = COUNTROWS ( Orders )

Delivered Orders =
CALCULATE ( COUNTROWS ( Orders ), Orders[OrderStatus] IN { "Delivered", "Delivered Late" } )

Late Orders = CALCULATE ( COUNTROWS ( Orders ), Orders[OrderStatus] = "Delivered Late" )

% Late Deliveries = DIVIDE ( [Late Orders], [Delivered Orders] )

Cancelled Orders = CALCULATE ( COUNTROWS ( Orders ), Orders[OrderStatus] = "Cancelled" )

Cancellation Rate = DIVIDE ( [Cancelled Orders], [Total Orders] )

-- 180 min is the cap applied in cleaning, not a real delivery time
Avg Delivery Time (min) =
CALCULATE (
    AVERAGE ( Orders[DeliveryTimeMinutes] ),
    Orders[OrderStatus] IN { "Delivered", "Delivered Late" },
    Orders[DeliveryTimeMinutes] < 180
)

Avg Rating =
AVERAGEX ( Feedback, ( Feedback[CustomerRating] + Feedback[DeliveryRating] + Feedback[FoodRating] ) / 3 )

Customers = DISTINCTCOUNT ( Orders[CustomerID] )

Active Customers =
VAR EndDate = MAX ( 'Date'[Date] )
RETURN
    CALCULATE ( [Customers], DATESINPERIOD ( 'Date'[Date], EndDate, -90, DAY ) )

Repeat Customers =
VAR CustomerOrders =
    ADDCOLUMNS ( VALUES ( Orders[CustomerID] ), "@Orders", CALCULATE ( COUNTROWS ( Orders ) ) )
RETURN
    COUNTROWS ( FILTER ( CustomerOrders, [@Orders] >= 2 ) )

Customer Retention Rate = DIVIDE ( [Repeat Customers], [Customers] )

New Customers =
VAR PeriodStart = MIN ( 'Date'[Date] )
VAR PeriodEnd = MAX ( 'Date'[Date] )
VAR FirstOrders =
    ADDCOLUMNS (
        VALUES ( Orders[CustomerID] ),
        "@FirstOrder", CALCULATE ( MIN ( Orders[OrderDate] ), REMOVEFILTERS ( 'Date' ) )
    )
RETURN
    COUNTROWS ( FILTER ( FirstOrders, [@FirstOrder] >= PeriodStart && [@FirstOrder] <= PeriodEnd ) )

Cumulative Customers =
CALCULATE ( [Customers], FILTER ( ALL ( 'Date' ), 'Date'[Date] <= MAX ( 'Date'[Date] ) ) )

Coupon Orders = CALCULATE ( [Total Orders], Orders[CouponCode] <> "NONE" )

Coupon Usage % = DIVIDE ( [Coupon Orders], [Total Orders] )

Total Discount =
CALCULATE ( SUM ( Orders[Discount] ), Orders[OrderStatus] IN { "Delivered", "Delivered Late" } )

Avg Order Value = DIVIDE ( [Total Revenue], [Delivered Orders] )

Churn Customers = COUNTROWS ( ChurnScores )

Actual Churn Rate = AVERAGE ( ChurnScores[Churn] )
```

**Formats** (*Measure tools → Format*):
- `Total Revenue`, `Total Discount`, `Avg Order Value`: Currency ₹, 0 decimals
- `%` measures, `Cancellation Rate`, `Customer Retention Rate`, `Actual Churn Rate`: Percentage, 1 decimal
- `Avg Delivery Time (min)`, `Avg Rating`: 1 decimal

## 7. Theme and layout rules

- *View → Themes → Browse for themes* → `powerbi/zomato_theme.json`.
- Use the same KPI card style on every page: *Format painter* from the first card.
- **Slicers:** add `Cities[City]` and `Date[Date]` (style *Between*) on page 1. Then *View → Sync slicers* to pages 2–5. The ML page has no date slicer, because the models are a single snapshot.
- **Tooltips:** add secondary measures to the *Tooltips* field well instead of extra visuals. For example, add `Delivered Orders` and `% Late Deliveries` to delivery-time charts.
- Give every visual a title and axis labels (NFR-06).

## 8. Pages

### Page 1: Executive Dashboard
- **KPI cards:** `Total Revenue`, `Total Orders`, `Avg Delivery Time (min)`, `Avg Rating`, `Active Customers`, `% Late Deliveries`
- **Line chart:** `Date[MonthStart]` × `Total Revenue`
- **Bar chart:** `Cities[City]` × `Total Revenue` (top 10: *Filters → Top N*)
- **Slicers:** City, Date

### Page 2: Customer Analytics
- **KPI cards:** `Customers`, `Customer Retention Rate`, `New Customers`
- **Donut:** `ChurnScores[RFM_Segment]` × `Churn Customers` (new / repeat / at-risk segments)
- **Line chart:** `Date[MonthStart]` × `New Customers` and `Cumulative Customers` (customer growth)
- **CLV distribution:** right-click `Customers[Lifetime Value]` → *New group* → Bin, size 250. Then a column chart of the bins × count of `CustomerID`. Filter out blank.

### Page 3: Restaurant Analytics
- **Table (Top 10):** `RestaurantScores` columns `City`, `CityRank`, `RestaurantName`, `Cuisine`, `CompositeScore`, `Rating`, `CancellationRate`, `LateRate`. Filter `PerformanceBand = Top 10`.
- **Table (Bottom 10):** same columns, with `CityRankFromBottom` and `PerformanceBand = Bottom 10`
- **Bar chart:** `Restaurants[Cuisine]` × `Total Revenue`
- **Bar chart:** `Restaurants[Cuisine]` × `Avg Rating`
- **Note (text box):** "Scorecard city = restaurant's city; revenue city = customer's city."

### Page 4: Delivery Analytics
- **Leaderboard table:** `DeliveryPartners[Name]`, `VehicleType`, `Rating`, `CompletedDeliveries`, `Delivered Orders`, `Avg Delivery Time (min)`, `% Late Deliveries`. Sort by `Avg Delivery Time (min)` ascending.
- **Line chart:** `Date[MonthStart]` × `Avg Delivery Time (min)`
- **Column chart (traffic impact):** `Orders[TrafficScore]` × `Avg Delivery Time (min)`
- **Column chart (rain impact):** `Orders[Rain]` × `Avg Delivery Time (min)`

### Page 5: Sales Dashboard
- **Line chart:** `Date` hierarchy (Year → Month → Day) × `Total Revenue`. Drill down for daily.
- **KPI cards:** `Coupon Usage %`, `Total Discount`, `Avg Order Value`
- **Clustered column:** `Date[MonthStart]` × `Coupon Orders` and `Total Discount` (secondary axis)
- **Donut:** `Orders[PaymentMethod]` × `Total Revenue`

### Page 6: ML Dashboard
- **Delivery model, scatter:** X = `DeliveryPredictions[Actual]`, Y = `DeliveryPredictions[Predicted]`, Values = `OrderID`, all set to *Don't summarize*
- **Delivery model, bar:** `DeliveryImportance[Feature]` × `Importance`
- **Delivery model, table:** `DeliveryModels` (MAE, MSE, RMSE, R²)
- **Churn model, donut:** `ChurnScores[RiskSegment]` × `Churn Customers`
- **Churn model, bar:** `ChurnDrivers[Feature]` × `Importance` (top churn drivers)
- **Churn model, table:** `ChurnModels` (Accuracy, Precision, Recall, F1, ROC-AUC)
- **Text box:** "Both models score close to their baseline (delivery R² ≈ 0, churn ROC-AUC ≈ 0.52 in CV), so the feature rankings do not show real drivers."

## 9. Refresh check

1. Run `python src/pipeline.py` on the Mac. If you copied the files instead of sharing the folder, re-copy the `data` folder.
2. In Power BI, click *Home → Refresh*. Every page should update without editing any query.
3. Sanity check with no filters applied. These values were calculated in Python with the same definitions:

| Measure | Expected |
|---|---|
| Total Revenue | ₹53,08,590 |
| Total Orders / Delivered Orders | 20,475 / 13,544 |
| % Late Deliveries | 15.9% |
| Cancellation Rate | 22.3% |
| Avg Delivery Time (min) | 38.3 |
| Avg Rating | 3.52 |
| Active Customers (90 days to 31 Dec 2024) | 2,258 |
| Customers / Customer Retention Rate | 9,827 / 62.2% |
| Coupon Usage % | 35.2% |
| Total Discount | ₹5,07,794 |
| Avg Order Value | ₹392 |

If a number doesn't match, check that measure's filter and the column's data type first.
