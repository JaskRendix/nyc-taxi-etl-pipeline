import json
import os
import pickle
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
MODEL_PATH = PROJECT_ROOT / "backend" / "core" / "fare_model.pkl"
METRICS_PATH = PROJECT_ROOT / "backend" / "core" / "metrics.json"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_data_from_db(config: dict[str, Any]) -> pd.DataFrame:
    # Check environment variable first, then config dict fallback
    url = (
        os.getenv("DB_URI")
        or config.get("database", {}).get("url")
        or config.get("database", {}).get("uri")
    )
    if not url:
        raise KeyError("Database URL not found in environment variables or config.yaml")

    engine = create_engine(url)
    query = "SELECT * FROM yellowcab_cleaned"
    df = pd.read_sql(query, engine)
    return df


def build_feature_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.dropna(
        subset=[
            "fare_amount",
            "trip_distance",
            "trip_duration",
            "hour",
            "passenger_count",
            "distance_bucket",
            "duration_bucket",
            "speed_mpm",
            "is_peak_hour",
            "is_airport",
        ]
    ).copy()

    feature_cols = [
        "trip_distance",
        "trip_duration",
        "hour",
        "passenger_count",
        "distance_bucket",
        "duration_bucket",
        "speed_mpm",
        "is_peak_hour",
        "is_airport",
    ]
    X = df[feature_cols]
    y = df["fare_amount"]

    return X, y


def train_model(
    X: pd.DataFrame, y: pd.Series
) -> tuple[LinearRegression, dict[str, float]]:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    r2 = r2_score(y_test, y_pred)

    metrics = {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
    }

    return model, metrics


def save_artifacts(model: LinearRegression, metrics: dict[str, float]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save the trained model binary via pickle
    with MODEL_PATH.open("wb") as f:
        pickle.dump(model, f)

    # Save evaluation metrics as JSON
    with METRICS_PATH.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)


def main() -> None:
    config = load_config()
    df = load_data_from_db(config)

    X, y = build_feature_target(df)
    model, metrics = train_model(X, y)
    save_artifacts(model, metrics)

    print("Model trained and saved to:", MODEL_PATH)
    print("Metrics saved to:", METRICS_PATH)
    print("Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")


if __name__ == "__main__":
    main()
