#src/export_powerbi.py
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
import numpy as np
import pandas as pd
from ingest import BASE_DIR, load_clean_dataset

PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

# Composite restaurant score weights (same formula as vw_restaurant_composite_score in sql/business_queries.sql)
RATING_WEIGHT = Fraction(4, 10)
CANCELLATION_WEIGHT = Fraction(3, 10)
LATE_WEIGHT = Fraction(3, 10)


def round_half_up(value, places: str) -> float:
    """Round like PostgreSQL NUMERIC (halves away from zero), not Python's banker's rounding."""
    return float(Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP))


def composite_score(rating: float, cancelled: int, late: int, delivered: int, total: int) -> float:
    """Exact score out of 100, rounded to 2 decimals (matches the SQL view to the cent)."""
    late_rate = Fraction(late, delivered) if delivered else Fraction(0)
    score = 100 * (RATING_WEIGHT * (Fraction(Decimal(str(rating))) - 1) / 4
                   + CANCELLATION_WEIGHT * (1 - Fraction(cancelled, total))
                   + LATE_WEIGHT * (1 - late_rate))
    return float((score * 100 + Fraction(1, 2)) // 1 / 100)


def build_restaurant_scores() -> pd.DataFrame:
    """
    Composite score out of 100 per restaurant (User Story 2):
    40% rating (1-5 rescaled to 0-1) + 30% (1 - cancellation rate) + 30% (1 - late delivery rate).
    Late rate is measured over delivered orders only.
    """
    orders = load_clean_dataset('orders_cleaned.csv')[['OrderID', 'RestaurantID', 'OrderStatus']]
    restaurants = load_clean_dataset('restaurants_cleaned.csv')[
        ['RestaurantID', 'RestaurantName', 'City', 'Cuisine', 'Rating']
    ]
    orders['RestaurantID'] = pd.to_numeric(orders['RestaurantID'], errors='coerce').astype('Int64')
    restaurants['RestaurantID'] = pd.to_numeric(restaurants['RestaurantID'], errors='coerce').astype('Int64')
    # Stored as NUMERIC(2,1) in the database; a few city-median imputed ratings have 2 decimals
    # (rounded from the raw text: pandas' float parser can turn 3.8499999999999996 into 3.85)
    restaurants['Rating'] = restaurants['Rating'].map(lambda r: round_half_up(r, '0.1'))

    delivered = orders['OrderStatus'].isin(['Delivered', 'Delivered Late'])
    orders['IsCancelled'] = (orders['OrderStatus'] == 'Cancelled').astype(int)
    orders['IsDelivered'] = delivered.astype(int)
    orders['IsLate'] = (orders['OrderStatus'] == 'Delivered Late').astype(int)

    stats = orders.groupby('RestaurantID').agg(
        TotalOrders=('OrderID', 'size'),
        Cancelled=('IsCancelled', 'sum'),
        Delivered=('IsDelivered', 'sum'),
        Late=('IsLate', 'sum'),
    ).reset_index()
    stats['CancellationRate'] = stats['Cancelled'] / stats['TotalOrders']
    # Late rate is over delivered orders only
    stats['LateRate'] = (stats['Late'] / stats['Delivered'].replace(0, np.nan)).fillna(0)

    scores = restaurants.merge(stats, on='RestaurantID', how='inner', validate='one_to_one')
    scores['CompositeScore'] = [
        composite_score(r.Rating, r.Cancelled, r.Late, r.Delivered, r.TotalOrders)
        for r in scores.itertuples()
    ]
    scores = scores.drop(columns=['Cancelled', 'Delivered', 'Late'])

    city_scores = scores.groupby('City')['CompositeScore']
    scores['CityRank'] = city_scores.rank(ascending=False, method='min').astype(int)
    scores['CityRankFromBottom'] = city_scores.rank(ascending=True, method='min').astype(int)
    scores['PerformanceBand'] = np.select(
        [scores['CityRank'] <= 10, scores['CityRankFromBottom'] <= 10],
        ['Top 10', 'Bottom 10'], default='Middle',
    )
    for col in ['CancellationRate', 'LateRate']:
        scores[col] = scores[col].map(lambda v: round_half_up(v, '0.0001'))
    return scores.sort_values(['City', 'CityRank']).reset_index(drop=True)


def export_powerbi_tables() -> None:
    """Write the extra tables used by the Power BI dashboard to data/processed."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    scores = build_restaurant_scores()
    try:
        scores.to_csv(PROCESSED_DATA_DIR / 'restaurant_scores.csv', index=False)
    except OSError as e:
        print(f"Could not save restaurant scores: {e}")
        raise
    print(f"Saved data/processed/restaurant_scores.csv ({len(scores)} restaurants)")


if __name__ == "__main__":
    export_powerbi_tables()
