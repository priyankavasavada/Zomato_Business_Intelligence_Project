import re
import numpy as np
import pandas as pd
import pathlib 
# ==========================================
# CONFIGURATION & LOOKUPS
# ==========================================

PK_MAP = {
    'cities': 'CityID',
    'customers': 'CustomerID',
    'restaurants': 'RestaurantID',
    'menu': 'FoodItemID',
    'delivery_partners': 'DeliveryPartnerID',
    'promotions': 'PromotionID',
    'orders': 'OrderID',
    'order_items': 'OrderItemID',
    'payments': 'PaymentID',
    'customer_feedback': 'FeedbackID',
    'weather': 'WeatherID',
    'traffic': 'TrafficID',
}

OUTLIER_COLUMNS_MAP = {
    'orders': ['DeliveryTimeMinutes', 'Discount', 'GST', 'FinalAmount', 'FoodCost'],
    'restaurants': ['Rating', 'AverageCost'],
    'customers': ['Age', 'TotalOrders'],
    'menu': ['Price', 'Calories', 'PreparationTime'],
    'delivery_partners': ['AverageDeliveryTime','Age','CompletedDeliveries', 'Rating'],
    'traffic': ['AverageSpeed'],
    'weather': ['Temperature', 'Rainfall', 'Humidity'],
    'cities': ['Population'],
    'order_items': ['UnitPrice', 'TotalPrice', 'Quantity'],
}

CITY_MAPPING = {
    'bangalore': 'Bengaluru',
    'bengaluru': 'Bengaluru',
    'bangalore ': 'Bengaluru',
    'bengaluru ': 'Bengaluru',
    'baroda': 'Vadodara',
    'baroda ': 'Vadodara',
    'mumbai': 'Mumbai',
    'mumbai ': 'Mumbai',
    'bombay': 'Mumbai',
    'bombay ': 'Mumbai',
    'Bombay': 'Mumbai',
    'delhi': 'Delhi',
    'new delhi': 'Delhi',
    'delhi ': 'Delhi',
    'pune': 'Pune',
    'pune ': 'Pune',
    'hyderabad': 'Hyderabad',
    'hyderabad ': 'Hyderabad',
    'chennai': 'Chennai',
    'chennai ': 'Chennai',
    'coimbatore': 'Coimbatore',
    'coimbatore ': 'Coimbatore',
    'kolkata': 'Kolkata',
    'kolkata ': 'Kolkata',
    'calcutta': 'Kolkata',
    'calcutta ': 'Kolkata',
    'ahmedabad': 'Ahmedabad',
    'ahmedabad ': 'Ahmedabad',
    'surat': 'Surat',
    'surat ': 'Surat',
    'jaipur': 'Jaipur',
    'jaipur ': 'Jaipur',
    'madras': 'Chennai',
    'madras ': 'Chennai',
    'nashik': 'Nashik',
    'kochi': 'Kochi',
    'visakhapatnam': 'Visakhapatnam',
}

DATE_COLUMNS_MAP = {
    'orders': ['OrderDate', 'DeliveryDate'],
    'customers': ['RegistrationDate', 'DOB'],
    'delivery_partners': ['JoiningDate'],
    'promotions': ['StartDate', 'EndDate'],
    'payments': ['PaymentDate'],
    'customer_feedback': ['FeedbackDate'],
    'weather': ['Date'],
    'traffic': ['Date']
}

# Exact clock time-of-day columns to parse into HH:MM:SS
TIME_COLUMNS_MAP = {
    'orders': ['OrderTime', 'DeliveryTime'],
    'restaurants': ['OpeningTime', 'ClosingTime'],
    'payments': ['PaymentTime'],
    'traffic': ['RecordedTime']
}

# ==========================================
# 1. TEXT & FORMAT NORMALIZATION
# ==========================================


def clean_whitespace_and_case(
    df: pd.DataFrame, text_columns: list[str]
) -> pd.DataFrame:
  """Strips leading/trailing whitespace and converts string columns to Title Case."""
  df = df.copy()
  for col in text_columns:
    if col in df.columns:
      df[col] = df[col].astype(str).str.strip().str.title()
      df[col] = df[col].replace({'Nan': np.nan, 'None': np.nan, '': np.nan})
  return df


def standardize_cities(
    df: pd.DataFrame, city_col: str = 'City'
) -> pd.DataFrame:
  """Standardizes city names to a unified format using lower-case lookup matching."""
  df = df.copy()
  if city_col in df.columns:
    cleaned_col = df[city_col].astype(str).str.strip()
    lowercase_col = cleaned_col.str.lower()
    df[city_col] = lowercase_col.map(CITY_MAPPING).fillna(
        cleaned_col.str.title()
    )
    df[city_col] = df[city_col].replace(
        {'Nan': np.nan, 'None': np.nan, '': np.nan}
    )
  return df


def clean_phone_numbers(
    df: pd.DataFrame, phone_col: str = 'Phone'
) -> pd.DataFrame:
  """Cleans phone numbers by extracting digits and keeping valid 10-digit formats."""
  df = df.copy()
  if phone_col in df.columns:
    digits_only = df[phone_col].astype(str).str.replace(r'\D', '', regex=True)
    valid_mask = digits_only.str.len() == 10
    df[phone_col] = np.where(valid_mask, digits_only, np.nan)
  return df


def clean_pincodes(
    df: pd.DataFrame, pincode_col: str = 'Pincode'
) -> pd.DataFrame:
  """Ensures pincodes are formatted as 6-digit numeric strings."""
  df = df.copy()
  if pincode_col in df.columns:
    digits_only = df[pincode_col].astype(str).str.replace(r'\D', '', regex=True)
    valid_mask = digits_only.str.len() == 6
    df[pincode_col] = np.where(valid_mask, digits_only, np.nan)
  return df


def standardize_dates(
    df: pd.DataFrame, date_columns: list[str]
) -> pd.DataFrame:
  """Standardizes date columns to YYYY-MM-DD format."""
  df = df.copy()
  for col in date_columns:
    if col in df.columns:
      df[col] = pd.to_datetime(
          df[col], errors='coerce', format='mixed'
      ).dt.strftime('%Y-%m-%d')
  return df


def standardize_times(
    df: pd.DataFrame, time_columns: list[str]
) -> pd.DataFrame:
  """Standardizes time columns to HH:MM:SS format."""
  df = df.copy()
  for col in time_columns:
    if col in df.columns:
      parsed_times = pd.to_datetime(
          df[col].astype(str).str.strip(), format='mixed', errors='coerce'
      )
      df[col] = parsed_times.dt.strftime('%H:%M:%S')
      df[col] = df[col].replace({'NaT': np.nan, 'None': np.nan, '': np.nan})
  return df


# ==========================================
# 2. SCHEMA & TYPE CONVERSIONS
# ==========================================


def convert_to_float(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
  """Cleans currency symbols/commas and casts target columns to float."""
  df = df.copy()
  for col in columns:
    if col in df.columns:
      cleaned_series = (
          df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True).str.strip()
      )
      df[col] = pd.to_numeric(cleaned_series, errors='coerce').astype(float)
  return df


def convert_to_int(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
  """Casts numeric counts and ages to pandas Nullable Int64."""
  df = df.copy()
  for col in columns:
    if col in df.columns:
      cleaned_series = (
          df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True).str.strip()
      )
      numeric_vals = pd.to_numeric(cleaned_series, errors='coerce')
      df[col] = numeric_vals.round().astype('Int64')
  return df


def convert_ids_to_str(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
  """Normalizes primary and foreign keys to string format without decimal artifacts."""
  df = df.copy()
  for col in columns:
    if col in df.columns:
      cleaned_series = (
          df[col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
      )
      df[col] = cleaned_series.replace(
          {'nan': np.nan, 'None': np.nan, '': np.nan, '<NA>': np.nan}
      )
  return df


def apply_type_conversions(
    datasets: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
  """Applies explicit type mappings across all 12 loaded datasets."""
  float_mapping = {
      'restaurants': ['AverageCost', 'Rating', 'Latitude', 'Longitude'],
      'menu': ['Price', 'Calories', 'PreparationTime'],
      'promotions': ['DiscountPercentage'],
      'orders': [
          'FoodCost',
          'DeliveryTimeMinutes',
          'DeliveryFee',
          'Discount',
          'GST',
          'FinalAmount',
      ],
      'order_items': ['UnitPrice', 'TotalPrice'],
      'customer_feedback': ['CustomerRating', 'DeliveryRating', 'FoodRating'],
      'weather': ['Temperature', 'Rainfall', 'Humidity'],
      'traffic': ['AverageSpeed'],
      'cities': ['AverageIncome'],
  }

  int_mapping = {
      'customers': ['Age', 'TotalOrders'],
      'delivery_partners': ['Age', 'CompletedDeliveries'],
      'order_items': ['Quantity'],
      'cities': ['Population'],
  }

  id_mapping = {
      'cities': ['CityID'],
      'customers': ['CustomerID'],
      'restaurants': ['RestaurantID'],
      'menu': ['FoodItemID', 'RestaurantID'],
      'delivery_partners': ['DeliveryPartnerID'],
      'promotions': ['PromotionID'],
      'orders': ['OrderID', 'CustomerID', 'RestaurantID', 'DeliveryPartnerID'],
      'order_items': ['OrderItemID', 'OrderID', 'FoodItemID'],
      'payments': ['PaymentID', 'OrderID'],
      'customer_feedback': ['FeedbackID', 'OrderID'],
      'weather': ['WeatherID'],
      'traffic': ['TrafficID'],
  }

  for key, df in datasets.items():
    if key in float_mapping:
      df = convert_to_float(df, float_mapping[key])
    if key in int_mapping:
      df = convert_to_int(df, int_mapping[key])
    if key in id_mapping:
      df = convert_ids_to_str(df, id_mapping[key])
    datasets[key] = df

  return datasets


# ==========================================
# 3. NUMERIC VALIDATION & CALCULATIONS
# ==========================================


def handle_negative_values(
    df: pd.DataFrame, column: str, action: str = 'abs'
) -> pd.DataFrame:
  """Handles negative values via 'abs', 'null', or 'zero' strategies."""
  df = df.copy()
  if column in df.columns:
    numeric_series = pd.to_numeric(df[column], errors='coerce')

    if action == 'abs':
      df[column] = numeric_series.abs()
    elif action == 'null':
      df[column] = numeric_series.mask(numeric_series < 0, np.nan)
    elif action == 'zero':
      df[column] = numeric_series.clip(lower=0)
  return df


def enforce_numeric_bounds(
    df: pd.DataFrame, bounds: dict[str, tuple[float, float]]
) -> pd.DataFrame:
  """Sets numeric values outside (min_val, max_val) to NaN."""
  df = df.copy()
  for col, (min_val, max_val) in bounds.items():
    if col in df.columns:
      numeric_series = pd.to_numeric(df[col], errors='coerce')
      out_of_bounds = (numeric_series < min_val) | (numeric_series > max_val)
      df[col] = numeric_series.mask(out_of_bounds, np.nan)
  return df


def clean_order_items_financials(df: pd.DataFrame) -> pd.DataFrame:
  """Cleans UnitPrice and Quantity, then recalculates TotalPrice."""
  df = df.copy()
  if 'UnitPrice' in df.columns:
    df['UnitPrice'] = (
        pd.to_numeric(df['UnitPrice'], errors='coerce').abs().fillna(0.0)
    )

  if 'Quantity' in df.columns:
    df['Quantity'] = (
        pd.to_numeric(df['Quantity'], errors='coerce')
        .abs()
        .fillna(1)
        .astype(int)
    )

  df['TotalPrice'] = (df['UnitPrice'] * df['Quantity']).round(2)
  return df


def clean_orders_financials(df: pd.DataFrame) -> pd.DataFrame:
  """Cleans cost components and programmatically recalculates FinalAmount."""
  df = df.copy()
  for col in ['FoodCost', 'DeliveryFee', 'GST']:
    if col in df.columns:
      df[col] = pd.to_numeric(df[col], errors='coerce').abs().fillna(0.0)

  if 'Discount' in df.columns:
    df['Discount'] = (
        pd.to_numeric(df['Discount'], errors='coerce').clip(lower=0).fillna(0.0)
    )

  calculated_amount = (
      (df['FoodCost'] - df['Discount']) + df['DeliveryFee'] + df['GST']
  )
  df['FinalAmount'] = calculated_amount.clip(lower=0).round(2)
  return df


def validate_numeric_constraints(
    datasets: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
  """Applies negative value rules, financial recalculations, and domain bounds."""
  negative_rules = {
      'orders': [
          ('FoodCost', 'abs'),
          ('DeliveryFee', 'abs'),
          ('Discount', 'zero'),
          ('DeliveryTimeMinutes', 'abs'),
      ],
      'restaurants': [('AverageCost', 'abs')],
      'menu': [('Price', 'abs'), ('PreparationTime', 'abs')],
      'order_items': [
          ('UnitPrice', 'abs'),
          ('TotalPrice', 'abs'),
          ('Quantity', 'abs'),
      ],
      'delivery_partners': [
          ('AverageDeliveryTime', 'abs'),
          ('CompletedDeliveries', 'abs'),
      ],
      'traffic': [('AverageSpeed', 'abs')],
      'customers': [('Age', 'null')],
      'cities': [('Population', 'abs'), ('AverageIncome', 'abs')],
  }

  for key, rules in negative_rules.items():
    if key in datasets:
      for col, action in rules:
        datasets[key] = handle_negative_values(
            datasets[key], col, action=action
        )

  if 'orders' in datasets:
    datasets['orders'] = clean_orders_financials(datasets['orders'])

  if 'order_items' in datasets:
    datasets['order_items'] = clean_order_items_financials(
        datasets['order_items']
    )

  domain_bounds = {
      'customers': {'Age': (10, 100)},
      'delivery_partners': {'Age': (18, 70), 'Rating': (1.0, 5.0)},
      'restaurants': {'Rating': (1.0, 5.0)},
      'customer_feedback': {
          'CustomerRating': (1, 5),
          'DeliveryRating': (1, 5),
          'FoodRating': (1, 5),
      },
      'promotions': {'DiscountPercentage': (0, 100)},
      'weather': {'Humidity': (0, 100)},
      'traffic': {'AverageSpeed': (0, 200)},
  }

  for key, bounds in domain_bounds.items():
    if key in datasets:
      datasets[key] = enforce_numeric_bounds(datasets[key], bounds)

  return datasets


# ==========================================
# 4. DATASET-SPECIFIC TEXT CLEANERS
# ==========================================


def clean_restaurants_string_fields(df: pd.DataFrame) -> pd.DataFrame:
  text_cols = ['RestaurantName', 'Cuisine', 'Area', 'OwnerName', 'RestaurantType']
  df = clean_whitespace_and_case(df, text_cols)
  df = standardize_cities(df, 'City')
  return df


def clean_customers_string_fields(df: pd.DataFrame) -> pd.DataFrame:
  text_cols = ['Name', 'Gender','Membership','Email', 'State', 'PreferredCuisine']
  df = clean_whitespace_and_case(df, text_cols)
  df = standardize_cities(df, 'City')
  return df


def clean_delivery_partners_string_fields(df: pd.DataFrame) -> pd.DataFrame:
  text_cols = ['Name','Gender', 'VehicleType']
  df = clean_whitespace_and_case(df, text_cols)
  df = standardize_cities(df, 'City')
  return df


def clean_menu_string_fields(df: pd.DataFrame) -> pd.DataFrame:
  text_cols = ['FoodName', 'Category', 'Availability']
  df = clean_whitespace_and_case(df, text_cols)
  return df


def clean_cities_string_fields(df: pd.DataFrame) -> pd.DataFrame:
  text_cols = ['Region']
  df = clean_whitespace_and_case(df, text_cols)
  df = standardize_cities(df, 'City')
  return df


def clean_promotions_string_fields(df: pd.DataFrame) -> pd.DataFrame:
  text_cols = ['CouponCode', 'CampaignName']
  df = clean_whitespace_and_case(df, text_cols)
  return df


def clean_orders_string_fields(df: pd.DataFrame) -> pd.DataFrame:
  text_cols = ['OrderStatus', 'PaymentMethod', 'CouponCode']
  df = clean_whitespace_and_case(df, text_cols)
  return df


def clean_payments_string_fields(df: pd.DataFrame) -> pd.DataFrame:
  text_cols = ['PaymentMethod', 'PaymentStatus', 'TransactionID']
  df = clean_whitespace_and_case(df, text_cols)
  return df


def clean_feedback_string_fields(df: pd.DataFrame) -> pd.DataFrame:
  text_cols = ['Review', 'Sentiment']
  df = clean_whitespace_and_case(df, text_cols)
  return df


def clean_weather_string_fields(df: pd.DataFrame) -> pd.DataFrame:
  text_cols = ['WeatherCondition']
  df = clean_whitespace_and_case(df, text_cols)
  df = standardize_cities(df, 'City')
  return df


def clean_traffic_string_fields(df: pd.DataFrame) -> pd.DataFrame:
  text_cols = ['TrafficLevel']
  df = clean_whitespace_and_case(df, text_cols)
  df = standardize_cities(df, 'City')
  return df

# ==========================================
# 5. DUPLICATE REMOVAL & HANDLING OUTLIERS
# ==========================================


def remove_duplicates(
    df: pd.DataFrame, primary_key: str = None
) -> pd.DataFrame:
  """Removes duplicate rows based on Primary Key or full row matching."""
  df = df.copy()
  if primary_key and primary_key in df.columns:
    return df.drop_duplicates(subset=[primary_key], keep='first')
  return df.drop_duplicates(keep='first')

'''
def handle_outliers(
    df: pd.DataFrame,
    columns: list[str],
    lower_quantile: float = 0.25,
    upper_quantile: float = 0.75,
) -> pd.DataFrame:
  """Clips extreme numeric values to lower and upper percentile caps."""
  df = df.copy()
  for col in columns:
    if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
      # Drop NaNs temporarily to calculate valid quantiles
      valid_series = df[col].dropna()
      if not valid_series.empty:
        lower_bound = valid_series.quantile(lower_quantile)
        upper_bound = valid_series.quantile(upper_quantile)
        df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
  return df
'''

# ==========================================
# 6. MASTER ORCHESTRATION PIPELINE
# ==========================================


def clean_all_data(
    datasets: dict[str, pd.DataFrame] = None,
) -> dict[str, pd.DataFrame]:
  """Master pipeline function to run end-to-end cleaning across all 12 loaded datasets."""
  if datasets is None:
    from ingest import load_all_raw_datasets

    datasets = load_all_raw_datasets()

  if not datasets:
    raise ValueError(
        'Failed to load raw datasets. Ensure data/raw/ contains CSV files.'
    )

  cleaned = {}

  # Step 1: Text & String Field Transformations Across All 12 Datasets
  if 'restaurants' in datasets:
    cleaned['restaurants'] = clean_restaurants_string_fields(
        datasets['restaurants']
    )

  if 'customers' in datasets:
    cleaned['customers'] = clean_customers_string_fields(datasets['customers'])

  if 'delivery_partners' in datasets:
    cleaned['delivery_partners'] = clean_delivery_partners_string_fields(
        datasets['delivery_partners']
    )

  if 'menu' in datasets:
    cleaned['menu'] = clean_menu_string_fields(datasets['menu'])

  if 'cities' in datasets:
    cleaned['cities'] = clean_cities_string_fields(datasets['cities'])

  if 'promotions' in datasets:
    cleaned['promotions'] = clean_promotions_string_fields(
        datasets['promotions']
    )

  if 'orders' in datasets:
    cleaned['orders'] = clean_orders_string_fields(datasets['orders'])


  if 'payments' in datasets:
    cleaned['payments'] = clean_payments_string_fields(datasets['payments'])

  if 'customer_feedback' in datasets:
    cleaned['customer_feedback'] = clean_feedback_string_fields(
        datasets['customer_feedback']
    )

  if 'weather' in datasets:
    cleaned['weather'] = clean_weather_string_fields(datasets['weather'])

  if 'traffic' in datasets:
    cleaned['traffic'] = clean_traffic_string_fields(datasets['traffic'])

  # Fallback pass-through for any remaining unhandled keys
  for key, df in datasets.items():
    if key not in cleaned:
      cleaned[key] = df

  # Step 2: Date and Time Standardization Across All Datasets
  for key, df in cleaned.items():
        if key in DATE_COLUMNS_MAP:
            df = standardize_dates(df, DATE_COLUMNS_MAP[key])
        if key in TIME_COLUMNS_MAP:
            df = standardize_times(df, TIME_COLUMNS_MAP[key])
        cleaned[key] = df

  # Step 3: Schema Data Type Conversions (Floats, Nullable Ints, String IDs)
  cleaned = apply_type_conversions(cleaned)

  # Step 4: Numeric Constraints, Financial Recalculations & Domain Bounds
  cleaned = validate_numeric_constraints(cleaned)
  # Step 5: Deduplication ONLY (Outlier handling deferred to post-EDA)
  for key, df in cleaned.items():
    pk = PK_MAP.get(key, None)
    df = remove_duplicates(df, primary_key=pk)
    cleaned[key] = df

  return cleaned

def export_cleaned_datasets(
    datasets: dict[str, pd.DataFrame], output_dir: str = 'data/cleaned'
) -> None:
  """Saves all processed DataFrames into the target cleaned directory as CSVs."""
  out_path = pathlib.Path(output_dir)
  out_path.mkdir(parents=True, exist_ok=True)

  for name, df in datasets.items():
    
    file_name = name if name.endswith('_cleaned') else f'{name}_cleaned'
    file_path = out_path / f'{file_name}.csv'
    df.to_csv(file_path, index=False)
    print(f" Saved: {file_path}")
# ==========================================
# EXECUTION / TESTING ENTRYPOINT
# ==========================================

if __name__ == "__main__":
    from ingest import load_all_raw_datasets

    print("==================================================")
    print("  RUNNING COMPREHENSIVE PIPELINE DIAGNOSTIC TEST  ")
    print("==================================================\n")

    # 1. Load Raw Datasets
    raw_datasets = load_all_raw_datasets()
    print(f"✓ Loaded {len(raw_datasets)} raw datasets.\n")

    # --------------------------------------------------
    # TEST 1: Text & String Cleaners
    # --------------------------------------------------
    print("--- 1. Testing Text & String Cleaners ---")
    if 'restaurants' in raw_datasets:
        res = clean_restaurants_string_fields(raw_datasets['restaurants'])
        print(f"✓ restaurants: {res['City'].nunique()} unique cities (Sample: {res['City'].dropna().unique()[:3]})")

    if 'customers' in raw_datasets:
        cust = clean_customers_string_fields(raw_datasets['customers'])
        print(f"✓ customers: Valid 10-digit Phone count = {cust['Phone'].dropna().str.len().eq(10).sum()}")

    '''
    # --------------------------------------------------
    # TEST 2: Outlier Clipping Standalone (left for EDA phase)
    # --------------------------------------------------
    print("\n--- 2. Testing Outlier Clipping (Quantile vs IQR) ---")
    sample_outlier_df = pd.DataFrame({
        'DeliveryTimeMinutes': [10.0, 25.0, 30.0, 35.0, 40.0, 500.0, np.nan]
    })
    initial_rows = len(sample_outlier_df)
    clipped_df = handle_outliers(sample_outlier_df, ['DeliveryTimeMinutes'])

    max_val_before = sample_outlier_df['DeliveryTimeMinutes'].max()
    max_val_after = clipped_df['DeliveryTimeMinutes'].max()

    print(f"✓ Raw Max DeliveryTimeMinutes: {max_val_before}")
    print(f"✓ Clipped Max DeliveryTimeMinutes: {max_val_after}")
    print(f"✓ Row Count Preserved: {len(clipped_df) == initial_rows} ({len(clipped_df)} rows)")
    '''
    # --------------------------------------------------
    # TEST 3: Deduplication Standalone
    # --------------------------------------------------
    print("\n--- 3. Testing Deduplication ---")
    sample_dup_df = pd.DataFrame({
        'OrderID': ['ORD101', 'ORD102', 'ORD101', 'ORD103'],
        'FoodCost': [250, 400, 250, 150]
    })
    deduped_df = remove_duplicates(sample_dup_df, primary_key='OrderID')
    print(f"✓ Raw Row Count: {len(sample_dup_df)} | Deduplicated Row Count: {len(deduped_df)}")
    print(f"✓ Primary Key Unique: {deduped_df['OrderID'].is_unique}")

    # --------------------------------------------------
    # TEST 4: Full End-to-End Orchestrator (Steps 1 to 5)
    # --------------------------------------------------
    print("\n--- 4. Testing Master clean_all_data() Orchestrator ---")
    try:
        cleaned_all = clean_all_data(raw_datasets)
        print(f"✓ Master pipeline successfully processed all {len(cleaned_all)} datasets with zero errors!")
        
        if 'orders' in cleaned_all:
            orders_df = cleaned_all['orders']
            print(f"✓ Orders Final Row Count: {len(orders_df)}")
            print(f"✓ Orders Primary Key ('OrderID') Is Unique: {orders_df['OrderID'].is_unique}")
            print(f"✓ Orders 'FinalAmount' Dtype: {orders_df['FinalAmount'].dtype}")
            
    except Exception as e:
        print(f"❌ Orchestrator failed with error:\n{e}")
        raise e

    print("\n==================================================")
    print("         ALL DIAGNOSTIC TESTS PASSED!             ")
    print("==================================================")

    # --------------------------------------------------
    # TEST 3: Export Cleaned Datasets to data/cleaned/
    # --------------------------------------------------
    print("\n--- 3. Exporting Clean Baseline to data/cleaned/ ---")
    export_cleaned_datasets(cleaned_all, output_dir='data/cleaned')

    print("\n==================================================")
    print("    BASELINE CLEANING COMPLETE! READY FOR EDA     ")
    print("==================================================")