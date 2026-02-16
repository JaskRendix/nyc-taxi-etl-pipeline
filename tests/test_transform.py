import pandas as pd

from pipeline.transform import transform


def test_transform_adds_duration():
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": [pd.Timestamp("2020-01-01 10:00")],
            "tpep_dropoff_datetime": [pd.Timestamp("2020-01-01 10:10")],
            "fare_amount": [10],
            "trip_distance": [1.0],
        }
    )

    # minimal config for transform()
    config = {
        "anomaly_thresholds": {
            "short_expensive": {"duration": 5, "fare": 50},
            "long_duration": 180,
            "cheap_per_mile": 0.5,
        }
    }

    out = transform(df, config)
    assert "trip_duration" in out.columns
