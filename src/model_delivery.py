#src/model_delivery.py
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, RandomizedSearchCV, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor
from ingest import BASE_DIR, load_clean_dataset

PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
RANDOM_STATE = 42

TARGET = 'DeliveryTimeMinutes'
# clean.py caps DeliveryTimeMinutes at 180; rows at the cap are not real delivery times
CAPPED_VALUE = 180

NUMERIC_FEATURES = [
    'TrafficScore', 'RainImpact', 'PeakHour', 'WeekendOrder', 'OrderHour',
    'DeliveryEfficiency', 'BasketSize', 'MaxPrepTime', 'FoodCost',
]
CATEGORICAL_FEATURES = ['VehicleType']

PARAM_GRIDS = {
    'Decision Tree': {
        'model__max_depth': [3, 5, 8, 12, None],
        'model__min_samples_leaf': [1, 5, 20, 50],
    },
    'Random Forest': {
        'model__n_estimators': [100, 200, 300],
        'model__max_depth': [5, 10, 15, None],
        'model__min_samples_leaf': [1, 5, 20],
    },
    'Gradient Boosting': {
        'model__n_estimators': [100, 200, 300],
        'model__learning_rate': [0.01, 0.05, 0.1],
        'model__max_depth': [2, 3, 5],
    },
}


def load_delivery_data() -> pd.DataFrame:
    """Delivered orders with the engineered features from featured_orders plus basket and partner info."""
    orders = pd.read_parquet(PROCESSED_DATA_DIR / 'featured_orders.parquet')
    for col in ['OrderID', 'DeliveryPartnerID', TARGET, 'FoodCost']:
        orders[col] = pd.to_numeric(orders[col], errors='coerce')

    # Only delivered orders have a meaningful delivery time
    orders = orders.loc[orders['OrderStatus'].isin(['Delivered', 'Delivered Late'])]
    orders = orders.loc[orders[TARGET] < CAPPED_VALUE]

    # Basket size and longest preparation time per order
    items = load_clean_dataset('order_items_cleaned.csv')
    menu = load_clean_dataset('menu_cleaned.csv')
    items[['OrderID', 'FoodItemID', 'Quantity']] = items[['OrderID', 'FoodItemID', 'Quantity']].apply(
        pd.to_numeric, errors='coerce')
    menu[['FoodItemID', 'PreparationTime']] = menu[['FoodItemID', 'PreparationTime']].apply(
        pd.to_numeric, errors='coerce')
    items = items.merge(menu[['FoodItemID', 'PreparationTime']], on='FoodItemID', how='left',
                        validate='many_to_one')
    basket = items.groupby('OrderID').agg(BasketSize=('Quantity', 'sum'),
                                          MaxPrepTime=('PreparationTime', 'max')).reset_index()
    orders = orders.merge(basket, on='OrderID', how='left', validate='one_to_one')

    partners = load_clean_dataset('delivery_partners_cleaned.csv')[['DeliveryPartnerID', 'VehicleType']]
    partners['DeliveryPartnerID'] = pd.to_numeric(partners['DeliveryPartnerID'], errors='coerce')
    orders = orders.merge(partners, on='DeliveryPartnerID', how='left', validate='many_to_one')

    return orders[['OrderID'] + NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET]].reset_index(drop=True)


def split_data(df: pd.DataFrame, test_size: float = 0.2):
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET]
    return train_test_split(X, y, test_size=test_size, random_state=RANDOM_STATE)


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ('num', StandardScaler(), NUMERIC_FEATURES),
        ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES),
    ])


def get_models() -> dict:
    return {
        'Baseline (mean)': DummyRegressor(strategy='mean'),
        'Linear Regression': LinearRegression(),
        'Decision Tree': DecisionTreeRegressor(max_depth=8, random_state=RANDOM_STATE),
        # n_jobs left at default: CV and the search already run folds in parallel
        'Random Forest': RandomForestRegressor(n_estimators=200, max_depth=10,
                                               random_state=RANDOM_STATE),
        'Gradient Boosting': GradientBoostingRegressor(random_state=RANDOM_STATE),
    }


def make_pipeline(model) -> Pipeline:
    return Pipeline([('prep', build_preprocessor()), ('model', model)])


def evaluate(pipe, X_test, y_test) -> dict:
    y_pred = pipe.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    return {
        'MAE': mean_absolute_error(y_test, y_pred),
        'MSE': mse,
        'RMSE': np.sqrt(mse),
        'R2': r2_score(y_test, y_pred),
    }


def cross_validate_models(X_train, y_train, n_splits: int = 5) -> pd.DataFrame:
    """k-fold CV on the training set for every model."""
    cv = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    rows = []
    for name, model in get_models().items():
        scores = cross_validate(make_pipeline(model), X_train, y_train, cv=cv, n_jobs=-1,
                                scoring=['neg_root_mean_squared_error', 'r2'])
        rows.append({
            'Model': name,
            'CV RMSE': -scores['test_neg_root_mean_squared_error'].mean(),
            'CV RMSE std': scores['test_neg_root_mean_squared_error'].std(),
            'CV R2': scores['test_r2'].mean(),
        })
    return pd.DataFrame(rows).set_index('Model').round(3)


def train_and_compare(X_train, X_test, y_train, y_test):
    """Fit every model on the full training set and score it on the test set."""
    results, fitted = [], {}
    for name, model in get_models().items():
        pipe = make_pipeline(model)
        try:
            pipe.fit(X_train, y_train)
        except Exception as e:
            print(f"{name} failed to train: {e}")
            continue
        results.append({'Model': name, **evaluate(pipe, X_test, y_test)})
        fitted[name] = pipe
    return pd.DataFrame(results).set_index('Model').round(3), fitted


def tune_models(names, X_train, y_train, n_iter: int = 10):
    """RandomizedSearchCV (3-fold, RMSE) for the given tree models."""
    tuned, best_params = {}, {}
    for name in names:
        search = RandomizedSearchCV(
            make_pipeline(get_models()[name]), PARAM_GRIDS[name], n_iter=n_iter, cv=3,
            scoring='neg_root_mean_squared_error', n_jobs=-1, random_state=RANDOM_STATE,
        )
        search.fit(X_train, y_train)
        tuned[f'{name} (tuned)'] = search.best_estimator_
        best_params[name] = {k.replace('model__', ''): v for k, v in search.best_params_.items()}
    return tuned, best_params


def get_feature_importance(pipe) -> pd.DataFrame:
    """Built-in feature importance of a tree-based pipeline, using the encoded column names."""
    names = pipe.named_steps['prep'].get_feature_names_out()
    names = [n.split('__', 1)[1] for n in names]
    importance = pd.DataFrame({'Feature': names,
                               'Importance': pipe.named_steps['model'].feature_importances_})
    return importance.sort_values('Importance', ascending=False).reset_index(drop=True)


def save_outputs(pipe, predictions: pd.DataFrame, importance: pd.DataFrame) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        joblib.dump(pipe, MODELS_DIR / 'delivery_time_best_model.pkl')
        predictions.to_csv(PROCESSED_DATA_DIR / 'delivery_predictions.csv', index=False)
        importance.to_csv(PROCESSED_DATA_DIR / 'delivery_feature_importance.csv', index=False)
    except OSError as e:
        print(f"Could not save delivery outputs: {e}")
        raise
    print("Saved models/delivery_time_best_model.pkl, data/processed/delivery_predictions.csv "
          "and data/processed/delivery_feature_importance.csv")


def train_delivery_model():
    """End-to-end: data -> CV -> test comparison -> tune top 2 tree models -> save best."""
    df = load_delivery_data()
    X_train, X_test, y_train, y_test = split_data(df)
    print(f"Delivered orders: {len(df)} | Train: {len(X_train)} | Test: {len(X_test)}")

    cv_results = cross_validate_models(X_train, y_train)
    print(cv_results.to_string())

    comparison, fitted = train_and_compare(X_train, X_test, y_train, y_test)

    tree_models = cv_results.loc[['Decision Tree', 'Random Forest', 'Gradient Boosting']]
    to_tune = tree_models.sort_values('CV RMSE').index[:2].tolist()
    tuned, best_params = tune_models(to_tune, X_train, y_train)
    for name, pipe in tuned.items():
        comparison.loc[name] = pd.Series(evaluate(pipe, X_test, y_test)).round(3)
        fitted[name] = pipe
    print(comparison.to_string())

    best_name = comparison.drop(index='Baseline (mean)')['RMSE'].idxmin()
    best_pipe = fitted[best_name]
    print(f"Best model (test RMSE): {best_name}")

    best_tree = comparison.loc[[n for n in comparison.index if n.endswith('(tuned)')], 'RMSE'].idxmin()
    importance = get_feature_importance(fitted[best_tree])

    predictions = pd.DataFrame({'OrderID': df.loc[X_test.index, 'OrderID'],
                                'Actual': y_test, 'Predicted': best_pipe.predict(X_test)})
    save_outputs(best_pipe, predictions, importance)
    return comparison, best_name


if __name__ == "__main__":
    train_delivery_model()
