import pandas as pd


def transform(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    thresholds = config["anomaly_thresholds"]

    df["trip_duration"] = (
        df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60

    df = df[(df["trip_duration"] > 0) & (df["fare_amount"] > 0)].copy()
    df["hour"] = df["tpep_pickup_datetime"].dt.hour

    # Add anomaly flags (optional)
    df["is_short_expensive"] = (
        df["trip_duration"] < thresholds["short_expensive"]["duration"]
    ) & (df["fare_amount"] > thresholds["short_expensive"]["fare"])

    df["is_long_duration"] = df["trip_duration"] > thresholds["long_duration"]

    df["is_cheap_per_mile"] = (df["fare_amount"] / df["trip_distance"]) < thresholds[
        "cheap_per_mile"
    ]

    return df
