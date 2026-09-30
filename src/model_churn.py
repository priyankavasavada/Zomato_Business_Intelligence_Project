#src/model_churn.py
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils.class_weight import compute_sample_weight
from ingest import BASE_DIR, load_clean_dataset

PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"

# Churn definition: no order in the next 60 days after the cut-off date
CHURN_WINDOW_DAYS = 60
RANDOM_STATE = 42
# Churn probability bands: Low <= 0.4 < Medium <= 0.6 < High
RISK_BANDS = [0, 0.4, 0.6, 1]

CANDIDATE_NUMERIC = [
    'RecencyDays', 'TenureDays', 'OrderCount', 'AvgOrderValue',
    'LateRate', 'FailedOrderRate', 'AvgDeliveryTime',
    'AvgRating', 'NegativeFeedbackRate',
    'CouponUsageRate', 'CODShare',
    'PeakHourShare', 'WeekendShare',
    'Age',
]
# NegativeFeedbackRate is dropped: correlation 0.81 with AvgRating (see notebook, Step 2)
NUMERIC_FEATURES = [c for c in CANDIDATE_NUMERIC if c != 'NegativeFeedbackRate']
CATEGORICAL_FEATURES = ['Gender', 'Membership', 'Region']


def load_orders() -> pd.DataFrame:
    """Cleaned orders with the per-order flags needed to build customer features."""
    orders = load_clean_dataset('orders_cleaned.csv')

    for col in ['OrderID', 'CustomerID']:
        orders[col] = pd.to_numeric(orders[col], errors='coerce').astype('Int64')
    for col in ['FinalAmount', 'Discount', 'DeliveryTimeMinutes']:
        orders[col] = pd.to_numeric(orders[col], errors='coerce')
    orders['OrderDate'] = pd.to_datetime(orders['OrderDate'], format='%Y-%m-%d', errors='coerce')
    orders = orders.dropna(subset=['CustomerID', 'OrderDate']).reset_index(drop=True)

    # Order status flags
    orders['IsLate'] = (orders['OrderStatus'] == 'Delivered Late').astype(int)
    orders['IsFailed'] = orders['OrderStatus'].isin(['Cancelled', 'Food Not Delivered']).astype(int)
    # Cancelled orders also carry a DeliveryTimeMinutes value, so keep it only for delivered orders
    is_delivered = orders['OrderStatus'].isin(['Delivered', 'Delivered Late'])
    orders['DeliveredTime'] = orders['DeliveryTimeMinutes'].where(is_delivered)

    orders['UsedCoupon'] = (orders['Discount'] > 0).astype(int)
    orders['IsCOD'] = (orders['PaymentMethod'] == 'Cash On Delivery').astype(int)

    # PeakHour / WeekendOrder were already engineered in features.py
    flags = pd.read_parquet(PROCESSED_DATA_DIR / 'featured_orders.parquet',
                            columns=['OrderID', 'PeakHour', 'WeekendOrder'])
    flags['OrderID'] = pd.to_numeric(flags['OrderID'], errors='coerce').astype('Int64')
    orders = orders.merge(flags, on='OrderID', how='left', validate='one_to_one')

    # Feedback: one rating per order (mean of the three ratings); a few orders have 2 reviews
    feedback = load_clean_dataset('customer_feedback_cleaned.csv')
    feedback['OrderID'] = pd.to_numeric(feedback['OrderID'], errors='coerce').astype('Int64')
    rating_cols = ['CustomerRating', 'DeliveryRating', 'FoodRating']
    feedback[rating_cols] = feedback[rating_cols].apply(pd.to_numeric, errors='coerce')
    feedback['OrderRating'] = feedback[rating_cols].mean(axis=1)
    feedback['IsNegative'] = (feedback['Sentiment'] == 'Negative').astype(int)
    feedback = feedback.groupby('OrderID').agg(OrderRating=('OrderRating', 'mean'),
                                               IsNegative=('IsNegative', 'max')).reset_index()
    orders = orders.merge(feedback, on='OrderID', how='left', validate='one_to_one')

    return orders


def build_churn_dataset(orders: pd.DataFrame, window_days: int = CHURN_WINDOW_DAYS):
    """
    One row per customer who ordered on or before the cut-off date.

    cut-off = last order date - window_days
    Churn   = 1 if the customer places no order in (cut-off, cut-off + window_days]
    Features use only orders on or before the cut-off.
    """
    cutoff = orders['OrderDate'].max() - pd.Timedelta(days=window_days)
    history = orders.loc[orders['OrderDate'] <= cutoff]
    future = orders.loc[orders['OrderDate'] > cutoff]

    dataset = history.groupby('CustomerID').agg(
        FirstOrder=('OrderDate', 'min'),
        LastOrder=('OrderDate', 'max'),
        OrderCount=('OrderID', 'size'),
        TotalSpend=('FinalAmount', 'sum'),
        AvgOrderValue=('FinalAmount', 'mean'),
        LateRate=('IsLate', 'mean'),
        FailedOrderRate=('IsFailed', 'mean'),
        AvgDeliveryTime=('DeliveredTime', 'mean'),
        AvgRating=('OrderRating', 'mean'),
        ReviewCount=('OrderRating', 'count'),
        NegativeCount=('IsNegative', 'sum'),
        CouponUsageRate=('UsedCoupon', 'mean'),
        CODShare=('IsCOD', 'mean'),
        PeakHourShare=('PeakHour', 'mean'),
        WeekendShare=('WeekendOrder', 'mean'),
    )

    dataset['RecencyDays'] = (cutoff - dataset['LastOrder']).dt.days
    dataset['TenureDays'] = (cutoff - dataset['FirstOrder']).dt.days
    # Undefined (NaN) for customers who never left a review
    dataset['NegativeFeedbackRate'] = dataset['NegativeCount'] / dataset['ReviewCount'].replace(0, np.nan)
    dataset['OrderCount'] = dataset['OrderCount'].astype(int)
    dataset = dataset.drop(columns=['FirstOrder', 'LastOrder', 'ReviewCount', 'NegativeCount'])

    # Profile attributes
    customers = load_clean_dataset('customers_cleaned.csv')[['CustomerID', 'Age', 'Gender', 'Membership', 'City']]
    customers['CustomerID'] = pd.to_numeric(customers['CustomerID'], errors='coerce').astype('Int64')
    customers['Age'] = pd.to_numeric(customers['Age'], errors='coerce')
    cities = load_clean_dataset('cities_cleaned.csv')[['City', 'Region']]
    profile = customers.merge(cities, on='City', how='left', validate='many_to_one').drop(columns='City')
    dataset = dataset.reset_index().merge(profile, on='CustomerID', how='left', validate='one_to_one')

    # Label
    dataset['Churn'] = (~dataset['CustomerID'].isin(future['CustomerID'])).astype(int)

    # Guard: features must not see any order after the cut-off
    assert history['OrderDate'].max() <= cutoff

    columns = ['CustomerID'] + CANDIDATE_NUMERIC + CATEGORICAL_FEATURES + ['TotalSpend', 'Churn']
    return dataset[columns], cutoff


def build_preprocessor() -> ColumnTransformer:
    """Impute + scale numeric columns, one-hot encode categorical columns."""
    numeric = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])
    categorical = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore')),
    ])
    return ColumnTransformer([
        ('num', numeric, NUMERIC_FEATURES),
        ('cat', categorical, CATEGORICAL_FEATURES),
    ])


def get_models() -> dict:
    """Baseline + the four classifiers required by the PRD."""
    return {
        'Dummy (always churn)': DummyClassifier(strategy='most_frequent'),
        'Logistic Regression': LogisticRegression(class_weight='balanced', max_iter=1000),
        'Decision Tree': DecisionTreeClassifier(class_weight='balanced', max_depth=5,
                                                random_state=RANDOM_STATE),
        'Random Forest': RandomForestClassifier(class_weight='balanced', n_estimators=300, max_depth=8,
                                                n_jobs=-1, random_state=RANDOM_STATE),
        # GradientBoosting has no class_weight, balanced sample weights are passed at fit time
        'Gradient Boosting': GradientBoostingClassifier(random_state=RANDOM_STATE),
    }


def split_data(dataset: pd.DataFrame, test_size: float = 0.2):
    """Stratified train/test split (one row per customer, so a random split is safe)."""
    X = dataset[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = dataset['Churn']
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=RANDOM_STATE)


def train_and_compare(X_train, X_test, y_train, y_test):
    """Fit every model in its own pipeline and return (comparison table, fitted pipelines)."""
    results, fitted = [], {}

    for name, model in get_models().items():
        pipe = Pipeline([('prep', build_preprocessor()), ('model', model)])
        try:
            if isinstance(model, GradientBoostingClassifier):
                pipe.fit(X_train, y_train,
                         model__sample_weight=compute_sample_weight('balanced', y_train))
            else:
                pipe.fit(X_train, y_train)
        except Exception as e:
            print(f"{name} failed to train: {e}")
            continue

        y_pred = pipe.predict(X_test)
        y_prob = pipe.predict_proba(X_test)[:, 1]
        results.append({
            'Model': name,
            'Accuracy': accuracy_score(y_test, y_pred),
            'Precision': precision_score(y_test, y_pred, zero_division=0),
            'Recall': recall_score(y_test, y_pred),
            'F1': f1_score(y_test, y_pred),
            'F1 (Retained)': f1_score(y_test, y_pred, pos_label=0, zero_division=0),
            'ROC-AUC': roc_auc_score(y_test, y_prob),
        })
        fitted[name] = pipe

    comparison = pd.DataFrame(results).set_index('Model').round(3)
    return comparison, fitted


def pick_best_model(comparison: pd.DataFrame) -> str:
    """Highest ROC-AUC among the real models (F1 is inflated by the churn base rate)."""
    return comparison.drop(index='Dummy (always churn)', errors='ignore')['ROC-AUC'].idxmax()


def get_top_drivers(pipe, X_test, y_test, top_n: int = 10) -> pd.DataFrame:
    """Permutation importance on the test set, measured as the drop in ROC-AUC."""
    result = permutation_importance(pipe, X_test, y_test, scoring='roc_auc',
                                    n_repeats=10, random_state=RANDOM_STATE, n_jobs=-1)
    drivers = pd.DataFrame({
        'Feature': X_test.columns,
        'Importance': result.importances_mean,
        'Std': result.importances_std,
    })
    return drivers.sort_values('Importance', ascending=False).head(top_n).reset_index(drop=True)


def build_rfm_segments(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Rule-based RFM scores (1-5) and segments at the cut-off date.
    R: recency quintiles (more recent = higher), F: order count 1,2,3,4,5+, M: total spend quintiles.
    """
    rfm = dataset[['CustomerID', 'RecencyDays', 'OrderCount', 'TotalSpend']].copy()
    rfm['R'] = pd.qcut(rfm['RecencyDays'], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm['F'] = rfm['OrderCount'].clip(upper=5).astype(int)
    rfm['M'] = pd.qcut(rfm['TotalSpend'], 5, labels=[1, 2, 3, 4, 5]).astype(int)

    # Checked in order, first match wins
    conditions = [
        (rfm['R'] >= 4) & (rfm['F'] >= 3),
        (rfm['R'] >= 3) & (rfm['F'] >= 2),
        (rfm['R'] >= 4) & (rfm['F'] == 1),
        (rfm['R'] <= 2) & (rfm['F'] >= 2),
        (rfm['R'] <= 2) & (rfm['F'] == 1),
    ]
    segments = ['Champions', 'Loyal', 'New', 'At Risk', 'Lost']
    rfm['RFM_Segment'] = np.select(conditions, segments, default='Needs Attention')
    return rfm[['CustomerID', 'R', 'F', 'M', 'RFM_Segment']]


def score_customers(pipe, dataset: pd.DataFrame, test_ids) -> pd.DataFrame:
    """Churn probability for every customer, a Low/Medium/High risk band, and a test-set flag."""
    X = dataset[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    scores = dataset[['CustomerID', 'Churn']].copy()
    scores['ChurnProbability'] = pipe.predict_proba(X)[:, 1]
    # Fixed bands around the 0.5 decision threshold of the class-weighted model
    scores['RiskSegment'] = pd.cut(scores['ChurnProbability'], bins=RISK_BANDS,
                                   labels=['Low', 'Medium', 'High'], include_lowest=True)
    scores['InTestSet'] = scores['CustomerID'].isin(test_ids).astype(int)
    return scores.merge(build_rfm_segments(dataset), on='CustomerID', how='left', validate='one_to_one')


def save_outputs(pipe, scores: pd.DataFrame, dataset: pd.DataFrame) -> None:
    """Save the best pipeline (.pkl), the customer scores (CSV) and the modelling table (Parquet)."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        joblib.dump(pipe, MODELS_DIR / 'churn_best_model.pkl')
        scores.to_csv(PROCESSED_DATA_DIR / 'churn_scores.csv', index=False)
        dataset.to_parquet(PROCESSED_DATA_DIR / 'churn_dataset.parquet', index=False)
    except OSError as e:
        print(f"Could not save churn outputs: {e}")
        raise
    print(f"Saved models/churn_best_model.pkl, data/processed/churn_scores.csv "
          f"({len(scores)} customers) and data/processed/churn_dataset.parquet")


def train_churn_model():
    """End-to-end: dataset -> train/compare -> best model -> scores + RFM -> saved outputs."""
    orders = load_orders()
    dataset, cutoff = build_churn_dataset(orders)
    print(f"Cut-off: {cutoff.date()} | Customers: {len(dataset)} | Churn rate: {dataset['Churn'].mean():.3f}")

    X_train, X_test, y_train, y_test = split_data(dataset)
    comparison, fitted = train_and_compare(X_train, X_test, y_train, y_test)
    print(comparison.to_string())

    best_name = pick_best_model(comparison)
    best_pipe = fitted[best_name]
    print(f"Best model (ROC-AUC): {best_name}")

    test_ids = dataset.loc[X_test.index, 'CustomerID']
    scores = score_customers(best_pipe, dataset, test_ids)
    save_outputs(best_pipe, scores, dataset)
    return comparison, best_name


if __name__ == "__main__":
    train_churn_model()
