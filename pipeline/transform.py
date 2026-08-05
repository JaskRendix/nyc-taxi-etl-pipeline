from collections.abc import Mapping
from typing import Any

import pandas as pd


def transform(df: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    """Transform and clean the raw NYC Taxi DataFrame based on configuration rules.

    Args:
        df: The raw pandas DataFrame extracted from source.
        config: A mapping containing configuration rules and anomaly thresholds.

    Returns:
        A cleaned and enriched pandas DataFrame with calculated metrics and anomaly flags.
    """
    thresholds: Mapping[str, Any] = config["anomaly_thresholds"]

    # Calculate basic trip duration in minutes
    df["trip_duration"] = (
        df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60

    # Filter out invalid durations and fares
    df = df[(df["trip_duration"] > 0) & (df["fare_amount"] > 0)].copy()
    df["hour"] = df["tpep_pickup_datetime"].dt.hour

    # Add anomaly flags
    df["is_short_expensive"] = (
        df["trip_duration"] < thresholds["short_expensive"]["duration"]
    ) & (df["fare_amount"] > thresholds["short_expensive"]["fare"])

    df["is_long_duration"] = df["trip_duration"] > thresholds["long_duration"]

    df["is_cheap_per_mile"] = (df["fare_amount"] / df["trip_distance"]) < thresholds[
        "cheap_per_mile"
    ]

    # Basic speed metric (miles per minute)
    df["speed_mpm"] = df["trip_distance"] / df["trip_duration"]

    # Peak hour flag (pulling from config, falling back to default commute windows)
    peak_hours = config.get("peak_hours", [7, 8, 9, 16, 17, 18])
    df["is_peak_hour"] = df["hour"].isin(peak_hours).astype(int)

    # Airport pickup flag (pulling from config)
    airport_zones = set(config.get("airport_zones", {1, 132, 138}))

    if "PULocationID" in df.columns:
        df["is_airport"] = df["PULocationID"].isin(airport_zones).astype(int)
    else:
        df["is_airport"] = 0

    # Distance buckets (categorical → numeric)
    df["distance_bucket"] = pd.cut(
        df["trip_distance"],
        bins=[-float("inf"), 1, 3, 7, 15, float("inf")],
        labels=[0, 1, 2, 3, 4],
        include_lowest=True,
    ).astype(int)

    # Duration buckets
    df["duration_bucket"] = pd.cut(
        df["trip_duration"],
        bins=[-float("inf"), 5, 10, 20, 40, float("inf")],
        labels=[0, 1, 2, 3, 4],
        include_lowest=True,
    ).astype(int)

    return df
