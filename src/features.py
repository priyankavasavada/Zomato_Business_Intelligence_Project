#src/features.py
import os
import numpy as np
import pandas as pd
from ingest import load_all_clean_datasets
def build_features():
    datasets = load_all_clean_datasets()
    # Print index position, type, and column names for each dataset
    if isinstance(datasets, dict):
        print("Dictionary keys:", datasets.keys())

    cities = datasets['cities_cleaned']
    customer_feedback = datasets['customer_feedback_cleaned']
    customers = datasets['customers_cleaned']
    delivery_partners = datasets['delivery_partners_cleaned']
    menu = datasets['menu_cleaned']
    order_items = datasets['order_items_cleaned']
    orders = datasets['orders_cleaned']
    payments = datasets['payments_cleaned']
    promotions = datasets['promotions_cleaned']
    restaurants = datasets['restaurants_cleaned']
    traffic = datasets['traffic_cleaned']
    weather = datasets['weather_cleaned']

    df_ord = orders.copy()
    # Peak Hour Feature Binary flag: 1 if OrderTime falls in lunch (12–2 PM) or dinner (7–10 PM) windows
    df_ord['OrderTimestamp'] = pd.to_datetime(
        df_ord['OrderDate'].astype(str) + ' ' + df_ord['OrderTime'].astype(str)
    )
    df_ord['OrderHour'] = df_ord['OrderTimestamp'].dt.hour
    df_ord['DayOfWeek'] = df_ord['OrderTimestamp'].dt.dayofweek

    # PeakHour: 1 if order falls in lunch (12-14) or dinner (19-22)
    df_ord['PeakHour'] = np.where(
        df_ord['OrderHour'].isin([12, 13, 14, 19, 20, 21, 22]), 1, 0
    )
    print(f"1. PeakHour engineered :\nDistribution : {df_ord['PeakHour'].value_counts().to_dict()}\n")

    # WeekendOrder : 1 if OrderDate falls on Saturday = 5 or Sunday = 6
    df_ord['WeekendOrder'] = np.where(
        df_ord['DayOfWeek'].isin([5,6]),1,0
    )
    print(f"2. WeekendOrder engineered :\nDistribution : {df_ord['WeekendOrder'].value_counts().to_dict()}\n")

    # Composite Merge for Weather (City + OrderDate)
    # Since City column exists in cities and linked to orders indirectly through customers, restaurants, delivery partners foreign keys
    if 'City' not in df_ord.columns:
      df_ord = df_ord.merge(
          customers[['CustomerID', 'City']], on='CustomerID', how='left'
      )

    if 'WeatherCondition' in weather.columns:
        date_col_w = 'OrderDate' if 'OrderDate' in weather.columns else 'Date'
        # weather.csv has multiple readings per City+Date (different sample
        # times), so it must be collapsed to one row per City+Date before
        # merging - otherwise every order fans out once per weather reading
        # for that city-day.
        weather_daily = (
            weather.groupby(['City', date_col_w])['WeatherCondition']
            .agg(lambda x: x.mode().iat[0] if not x.mode().empty else np.nan)
            .reset_index()
        )
        df_ord = df_ord.merge(
            weather_daily,
            left_on=['City', 'OrderDate'],
            right_on=['City', date_col_w],
            how='left'
        )
        if date_col_w != 'OrderDate':
            df_ord.drop(columns=[date_col_w], inplace=True)

    # RainImpact : Categorical/numeric score derived from weather.Rainfall on the order's date and city
    df_ord['WeatherCondition'] = df_ord['WeatherCondition'].fillna('Clear') 
    df_ord['RainImpact'] = np.where(
        df_ord['WeatherCondition'].str.contains('Rainy|Stormy', case=False, na=False), 1, 0
    )
    print(f"3. RainImpact engineered :\nDistribution : {df_ord['RainImpact'].value_counts().to_dict()}\n")

    # Merging for traffic score
    date_col_t = 'OrderDate' if 'OrderDate' in traffic.columns else 'Date'
    # traffic.csv has multiple readings per City+Date (different sample
    # times), so it must be collapsed to one row per City+Date before
    # merging - otherwise every order fans out once per traffic reading
    # for that city-day, compounding with the weather fan-out above.
    traffic_daily = (
        traffic.groupby(['City', date_col_t])['TrafficLevel']
        .agg(lambda x: x.mode().iat[0] if not x.mode().empty else np.nan)
        .reset_index()
    )
    df_ord = df_ord.merge(
        traffic_daily,
        left_on=['City', 'OrderDate'],
        right_on=['City', date_col_t],
        how='left',
    )
    if date_col_t != 'OrderDate':
      df_ord.drop(columns=[date_col_t], inplace=True)

    # TrafficScore : Numeric score derived from traffic.TrafficLevel at the order's time and city
    traffic_map = {'Low': 1, 'Moderate': 2, 'High': 3, 'Severe': 4}
    df_ord['TrafficScore'] = df_ord['TrafficLevel'].map(traffic_map)

    # Compute median traffic score from non-null records
    median_traffic_score = df_ord['TrafficScore'].median()

    # Fill missing records with median score
    df_ord['TrafficScore'] = (
        df_ord['TrafficScore'].fillna(median_traffic_score).astype(int)
    )

    print(f"4. TrafficScore engineered (Median = {int(median_traffic_score)}) :\nDistribution : {df_ord['TrafficScore'].value_counts().to_dict()}\n")

    # Merge RegistrationDate 
    if 'RegistrationDate' not in df_ord.columns and 'RegistrationDate' in customers.columns:
        df_ord = df_ord.merge(
            customers[['CustomerID', 'RegistrationDate']], 
            on='CustomerID', 
            how='left'
        )

    # CustomerTenure : Days between customers.RegistrationDate and the order date
    df_ord['RegistrationDate'] = pd.to_datetime(df_ord['RegistrationDate'])
    df_ord['CustomerTenure'] = (
        df_ord['OrderTimestamp'] - df_ord['RegistrationDate']
    ).dt.days.clip(lower=0)

    print(f"5. CustomerTenure engineered : \nMean: {df_ord['CustomerTenure'].mean():.1f} days\n"
        f"| Min: {df_ord['CustomerTenure'].min()} | Max: {df_ord['CustomerTenure'].max()}\n"
    )

    # Historical Aggregations from customers 
    # Changed to Leak-Free Historical Customer Aggregations (Expanding Windows)
    # AverageBasketValue : Mean FinalAmount per customer across all their orders
    # CustomerLifetimeValue : Cumulative FinalAmount per customer to date
    # OrderFrequency : Orders per customer per 30-day window

    df_ord = df_ord.sort_values('OrderTimestamp').reset_index(drop=True)
    df_ord['FinalAmount'] = pd.to_numeric(df_ord['FinalAmount'], errors='coerce')

    cust_groupby = df_ord.groupby('CustomerID')
    df_ord['CustomerLifetimeValue'] = (
        cust_groupby['FinalAmount']
        .transform(lambda x: x.shift(1).expanding().sum())
        .fillna(0)
    )

    df_ord['AverageBasketValue'] = (
        cust_groupby['FinalAmount']
        .transform(lambda x: x.shift(1).expanding().mean())
        .fillna(0)
    )

    df_ord['PriorOrderCount'] = cust_groupby['OrderID'].cumcount()
    first_order_dates = cust_groupby['OrderTimestamp'].transform('min')
    active_days = (df_ord['OrderTimestamp'] - first_order_dates).dt.days.clip(lower=1)

    df_ord['OrderFrequency'] = (
        (df_ord['PriorOrderCount'] / (active_days / 30))
        .round(2)
        .fillna(0)
    )

    # Clipped the orderfrequency to 90 orders/ 30 days to deal with outliers
    df_ord['OrderFrequency'] = df_ord['OrderFrequency'].clip(upper=90)
    df_ord.drop(columns=['PriorOrderCount'], inplace=True)

    print(f"6. AverageBasketValue engineered :\nMean Basket Value: ₹{df_ord['AverageBasketValue'].mean():.2f}\n")
    print(f"7. CustomerLifetimeValue engineered :\nMean CLV: ₹{df_ord['CustomerLifetimeValue'].mean():.2f}\n")
    print(f"8. OrderFrequency engineered :\nMean Frequency: {df_ord['OrderFrequency'].mean():.2f} orders/30 days\n")

    # RestaurantPopularity : Order count and revenue rank for a restaurant within its city
    # Changed to Leak-free RestaurantPopularity
    df_temp = df_ord.set_index('OrderTimestamp').sort_index()
    rolling_counts = (
        df_temp.groupby(['City', 'RestaurantID'])['OrderID']
        .rolling('30D')
        .count()
        .reset_index(name='RestaurantOrderCount_30D')
    )

    df_ord = df_ord.merge(
        rolling_counts,
        on=['City', 'RestaurantID', 'OrderTimestamp'],
        how='left'
    )

    df_ord['RestaurantPopularity'] = (
        df_ord.groupby(['City', 'OrderTimestamp'])['RestaurantOrderCount_30D']
        .rank(ascending=False, method='min')
    )

    df_ord.drop(columns=['RestaurantOrderCount_30D'], inplace=True)
    print(
        f"9. RestaurantPopularity engineered :\nMean City Rank: {df_ord['RestaurantPopularity'].mean():.1f}\n"
    )

    
    # Ensure data is chronologically sorted before expanding window transformations
    df_ord = df_ord.sort_values("OrderTimestamp").reset_index(drop=True)

    # Historical Driver Efficiency (Leak-Free)
    if (
        "DeliveryPartnerID" in df_ord.columns
        and "DeliveryTimeMinutes" in df_ord.columns
    ):
        # Driver's historical average delivery time prior to the current order
        driver_hist = df_ord.groupby("DeliveryPartnerID")[
            "DeliveryTimeMinutes"
            ].transform(lambda x: x.shift(1).expanding().mean())

        # City historical average delivery time prior to the current order
        city_hist = df_ord.groupby("City")["DeliveryTimeMinutes"].transform(
            lambda x: x.shift(1).expanding().mean()
            )

        # DeliveryEfficiency : Ratio of driver historical speed to city historical speed
        df_ord["DeliveryEfficiency"] = (
            (driver_hist / city_hist).round(2).fillna(1.0)
            )

    print(
        f"10. DeliveryEfficiency engineered :\nMean Index Ratio: {df_ord['DeliveryEfficiency'].mean():.2f}\n"
        f' | Min: {df_ord["DeliveryEfficiency"].min():.2f}'
        f' | Max: {df_ord["DeliveryEfficiency"].max():.2f}'
        f' | Std: {df_ord["DeliveryEfficiency"].std():.2f}\n'
    )

    # AverageRating : Mean of CustomerRating, DeliveryRating, and FoodRating per order/restaurant
    # 11. Leak-Free Historical AverageRating per Restaurant
    if 'OrderID' in customer_feedback.columns and 'RestaurantID' in df_ord.columns:
        rating_cols = [
            c for c in ['CustomerRating', 'DeliveryRating', 'FoodRating']
            if c in customer_feedback.columns
        ]
        
        if rating_cols:
            # Ensure rating columns are numeric
            feedback_clean = customer_feedback[['OrderID'] + rating_cols].copy()
            for col in rating_cols:
                feedback_clean[col] = pd.to_numeric(feedback_clean[col], errors='coerce')

            # Calculate average score for that specific order feedback
            feedback_clean['CurrentOrderRating'] = feedback_clean[rating_cols].mean(axis=1)

            # A small number of orders have more than one feedback submission
            # (same OrderID, different FeedbackID, so the primary-key dedup in
            # clean.py doesn't catch them). Collapse to one rating per OrderID
            # before merging so this doesn't fan out the order-level table.
            feedback_by_order = (
                feedback_clean.groupby('OrderID')['CurrentOrderRating']
                .mean()
                .reset_index()
            )

            # Merge feedback onto orders by OrderID
            df_ord = df_ord.merge(
                feedback_by_order,
                on='OrderID',
                how='left'
            )

            # Ensure chronological order before expanding window calculation
            df_ord = df_ord.sort_values('OrderTimestamp').reset_index(drop=True)

            # Calculate historical expanding mean rating per restaurant (excluding current order)
            rest_groupby = df_ord.groupby('RestaurantID')
            df_ord['AverageRating'] = (
                rest_groupby['CurrentOrderRating']
                .transform(lambda x: x.shift(1).expanding().mean())
                .round(2)
            )

            # Flag cold-start restaurants (so the model knows the rating is imputed)
            df_ord["is_new_restaurant"] = df_ord["AverageRating"].isna().astype(int)
            
            # Impute missing ratings with the city-wide historical median
            city_medians = df_ord.groupby("City")["AverageRating"].transform("median")
            df_ord["AverageRating"] = df_ord["AverageRating"].fillna(city_medians).fillna(4.0)

            # Clean up the temporary current order column
            df_ord.drop(columns=['CurrentOrderRating'], inplace=True)

            print(
                f"11. AverageRating engineered :\nMean Historical Rating: "
                f"{df_ord['AverageRating'].mean():.2f}/5.00 | Min: "
                f"{df_ord['AverageRating'].min():.2f} | Max: "
                f"{df_ord['AverageRating'].max():.2f}\n"
            )

    # Dropping columns to avoid cluttering
    columns_to_drop = ['TrafficLevel', 'WeatherCondition','CustomerRating','DeliveryRating','FoodRating']
    df_ord.drop(columns=[c for c in columns_to_drop if c in df_ord.columns], inplace=True)

    # Flag synthetic subscription spikes
    df_ord['is_synthetic_tier'] = df_ord['OrderFrequency'].isin([30, 60, 90]).astype(int)

    # Log transform frequency for linear models
    df_ord['OrderFrequency_Log'] = np.log1p(df_ord['OrderFrequency'])
        
    return df_ord

def export_featured_datasets(
    df: pd.DataFrame,
    base_dir: str = '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/processed',
    filename: str = 'featured_orders',
) -> None:

    # Making sure ouput directory exists
    os.makedirs(base_dir, exist_ok=True)

    csv_path = os.path.join(base_dir, f'{filename}.csv')
    parquet_path = os.path.join(base_dir, f'{filename}.parquet')

    # Export CSV (For Power BI / Manual Inspection)
    df.to_csv(csv_path, index=False)

    # Export Parquet (For Python ML models - preserves exact dtypes)
    df.to_parquet(parquet_path, index=False)

    print(f"Exported CSV and Parquet files with name : {filename} with ({df.shape[1]}) columns and {len(df)} records.")
    return df


if __name__ == "__main__":
    df_features = build_features()
    print("Feature engineering complete. Shape:", df_features.shape)
    df_save = export_featured_datasets(df_features)
