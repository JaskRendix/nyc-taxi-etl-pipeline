import pandas as pd

from pipeline.validate import validate


def test_validate_passes_clean_data():
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": [pd.Timestamp("2020-01-01 10:00")],
            "tpep_dropoff_datetime": [pd.Timestamp("2020-01-01 10:05")],
            "trip_distance": [1.0],
            "fare_amount": [10],
            "trip_duration": [5],
            "hour": [10],
        }
    )

    config = {
        "anomaly_thresholds": {
            "short_expensive": {"duration": 5, "fare": 50},
            "long_duration": 180,
            "cheap_per_mile": 0.5,
        }
    }

    validate(df, config)
