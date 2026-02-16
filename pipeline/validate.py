import logging

import pandas as pd


def validate(df: pd.DataFrame, config: dict) -> None:
    """
    Validate the cleaned DataFrame using rules from config.
    Raises ValueError if validation fails.
    """

    thresholds = config["anomaly_thresholds"]

    # Basic schema checks
    required_columns = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "trip_distance",
        "fare_amount",
        "trip_duration",
        "hour",
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Check for negative durations
    if (df["trip_duration"] <= 0).any():
        raise ValueError("Found non-positive trip durations")

    # Check for negative fares
    if (df["fare_amount"] <= 0).any():
        raise ValueError("Found non-positive fare amounts")

    # Optional: check anomaly thresholds make sense
    if thresholds["short_expensive"]["duration"] <= 0:
        raise ValueError("Invalid short_expensive.duration threshold")

    logging.info("Validation passed successfully")
