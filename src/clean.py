import pandas as pd
import numpy as np

# City Mapping Dictionary to fix spelling and capitalization variations
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
    'visakhapatnam': 'Visakhapatnam'
}

def clean_whitespace_and_case(df: pd.DataFrame, text_columns: list[str]) -> pd.DataFrame:
    """
    Strips leading/trailing whitespace and converts string columns to Title Case.
    """
    df = df.copy()
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
            # Restore true NaN/None values from string representations
            df[col] = df[col].replace({'Nan': np.nan, 'None': np.nan, '': np.nan})
    return df

def standardize_cities(df: pd.DataFrame, city_col: str = 'City') -> pd.DataFrame:
    """
    Standardizes city names to a unified format using lower-case lookup matching.
    """
    df = df.copy()
    if city_col in df.columns:
        # Strip whitespace first, then map via lowercase
        cleaned_col = df[city_col].astype(str).str.strip()
        lowercase_col = cleaned_col.str.lower()
        
        # Apply dictionary mapping, falling back to Title Case if not in map
        df[city_col] = lowercase_col.map(CITY_MAPPING).fillna(cleaned_col.str.title())
        df[city_col] = df[city_col].replace({'Nan': np.nan, 'None': np.nan, '': np.nan})
    return df

def clean_restaurants_string_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans all text fields specifically for the restaurants dataset.
    """
    text_cols = ['RestaurantName', 'Cuisine', 'Area', 'OwnerName', 'RestaurantType']
    df = clean_whitespace_and_case(df, text_cols)
    df = standardize_cities(df, 'City')
    return df

def clean_customers_string_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans text fields specifically for the customers dataset.
    """
    text_cols = ['Name', 'Area', 'State', 'PreferredCuisine']
    df = clean_whitespace_and_case(df, text_cols)
    df = standardize_cities(df, 'City')
    return df

def clean_delivery_partners_string_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans text fields specifically for the delivery partners dataset.
    """
    text_cols = ['Name']
    df = clean_whitespace_and_case(df, text_cols)
    df = standardize_cities(df, 'City')
    return df

def clean_menu_string_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans text fields specifically for the menu dataset.
    """
    text_cols = ['FoodName']
    df = clean_whitespace_and_case(df, text_cols)
    return df

def clean_all_data(datasets: dict[str, pd.DataFrame] = None) -> dict[str, pd.DataFrame]:
    """
    Master pipeline function to clean all loaded datasets.
    """
    if not datasets:
      raise ValueError("Failed to load raw datasets. Ensure data/raw/ contains CSV files.")

    cleaned = {}  
    
    # 1. Restaurants
    if 'restaurants' in datasets:
        df = clean_restaurants_string_fields(datasets['restaurants'])
        cleaned['restaurants'] = df
        
    # 2. Customers
    if 'customers' in datasets:
        df = clean_customers_string_fields(datasets['customers'])
        cleaned['customers'] = df

    # 3. Delivery Partners
    if 'delivery_partners' in datasets:
        df = clean_delivery_partners_string_fields(datasets['delivery_partners'])
        cleaned['delivery_partners'] = df

    # 4. Menu
    if 'menu' in datasets:
        df = clean_menu_string_fields(datasets['menu'])
        cleaned['menu'] = df

        
    # 5. Pass through remaining tables for now
    for key, df in datasets.items():
        if key not in cleaned:
            cleaned[key] = df
            
    return cleaned

if __name__ == "__main__":
    from ingest import load_raw_dataset
    
    print("=== Testing String & City Standardization ===")
    
    # Restaurants
    raw_rest = load_raw_dataset("restaurants.csv")
    cleaned_rest = clean_restaurants_string_fields(raw_rest)
    print(f"Restaurants raw unique cities count: {raw_rest['City'].nunique()}")
    print(f"Restaurants cleaned unique cities count: {cleaned_rest['City'].nunique()}")
    print("Cleaned Unique Cities:", cleaned_rest['City'].dropna().unique())

    # Customers
    raw_cust = load_raw_dataset("customers.csv")
    cleaned_cust = clean_customers_string_fields(raw_cust)
    print(f"Customers raw unique cities count: {raw_cust['City'].nunique()}")
    print(f"Customers cleaned unique cities count: {cleaned_cust['City']. nunique()}")
    print("Cleaned Unique Cities:", cleaned_cust['City'].dropna().unique())

    # Delivery Partners
    raw_dp = load_raw_dataset("delivery_partners.csv")
    cleaned_dp = clean_delivery_partners_string_fields(raw_dp)
    print(f"Delivery Partners raw unique cities count: {raw_dp['City'].nunique()}")
    print(f"Delivery Partners cleaned unique cities count: {cleaned_dp['City'].nunique()}")
    print("Cleaned Unique Cities:", cleaned_dp['City'].dropna().unique())
   