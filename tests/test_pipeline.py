from unittest.mock import patch

import pandas as pd
import pytest

from pipeline.extract import extract
from pipeline.load import load
from pipeline.transform import transform
from pipeline.validate import validate


@pytest.fixture
def config():
    return {
        "anomaly_thresholds": {
            "short_expensive": {"duration": 5, "fare": 50},
            "long_duration": 180,
            "cheap_per_mile": 0.5,
        }
    }


def test_extract_csv(tmp_path):
    csv = tmp_path / "test.csv"
    csv.write_text(
        "tpep_pickup_datetime,tpep_dropoff_datetime,trip_distance,fare_amount\n"
        "2020-01-01 10:00,2020-01-01 10:05,1.0,10\n"
    )

    df = extract(str(csv))
    assert len(df) == 1
    assert "tpep_pickup_datetime" in df.columns


def test_extract_parquet(tmp_path):
    df_in = pd.DataFrame(
        {
            "tpep_pickup_datetime": [pd.Timestamp("2020-01-01 10:00")],
            "tpep_dropoff_datetime": [pd.Timestamp("2020-01-01 10:05")],
            "trip_distance": [1.0],
            "fare_amount": [10],
        }
    )

    pq = tmp_path / "test.parquet"
    df_in.to_parquet(pq)

    df_out = extract(str(pq))
    assert len(df_out) == 1
    assert df_out.equals(df_in)


def test_extract_unsupported_extension():
    with pytest.raises(ValueError):
        extract("data.txt")


def test_transform_adds_duration(config):
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": [pd.Timestamp("2020-01-01 10:00")],
            "tpep_dropoff_datetime": [pd.Timestamp("2020-01-01 10:10")],
            "fare_amount": [10],
            "trip_distance": [1.0],
        }
    )

    out = transform(df, config)
    assert "trip_duration" in out.columns
    assert out["trip_duration"].iloc[0] == 10


def test_transform_filters_invalid_rows(config):
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": [pd.Timestamp("2020-01-01 10:00")],
            "tpep_dropoff_datetime": [pd.Timestamp("2020-01-01 10:10")],
            "fare_amount": [-5],  # invalid
            "trip_distance": [1.0],
        }
    )

    out = transform(df, config)
    assert len(out) == 0


def test_transform_adds_anomaly_flags(config):
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": [pd.Timestamp("2020-01-01 10:00")],
            "tpep_dropoff_datetime": [pd.Timestamp("2020-01-01 10:10")],
            "fare_amount": [100],
            "trip_distance": [1.0],
        }
    )

    out = transform(df, config)
    assert {"is_short_expensive", "is_long_duration", "is_cheap_per_mile"} <= set(
        out.columns
    )


def test_transform_extracts_hour(config):
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": [pd.Timestamp("2020-01-01 15:00")],
            "tpep_dropoff_datetime": [pd.Timestamp("2020-01-01 15:10")],
            "fare_amount": [10],
            "trip_distance": [1.0],
        }
    )

    out = transform(df, config)
    assert out["hour"].iloc[0] == 15


def test_validate_passes_clean_data(config):
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
    validate(df, config)  # should not raise


def test_validate_missing_column_raises(config):
    df = pd.DataFrame({"fare_amount": [10]})
    with pytest.raises(ValueError):
        validate(df, config)


def test_validate_rejects_non_positive_duration(config):
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": [pd.Timestamp("2020-01-01 10:00")],
            "tpep_dropoff_datetime": [pd.Timestamp("2020-01-01 10:05")],
            "trip_distance": [1.0],
            "fare_amount": [10],
            "trip_duration": [0],
            "hour": [10],
        }
    )
    with pytest.raises(ValueError):
        validate(df, config)


def test_validate_rejects_negative_fare(config):
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": [pd.Timestamp("2020-01-01 10:00")],
            "tpep_dropoff_datetime": [pd.Timestamp("2020-01-01 10:05")],
            "trip_distance": [1.0],
            "fare_amount": [-5],
            "trip_duration": [5],
            "hour": [10],
        }
    )
    with pytest.raises(ValueError):
        validate(df, config)


def test_validate_invalid_thresholds(config):
    config["anomaly_thresholds"]["short_expensive"]["duration"] = 0
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
    with pytest.raises(ValueError):
        validate(df, config)


def test_load_writes_csv(tmp_path):
    df = pd.DataFrame({"a": [1]})
    load(df, tmp_path, None)
    assert (tmp_path / "cleaned_output.csv").exists()


def test_load_writes_to_sql(tmp_path):
    df = pd.DataFrame({"a": [1]})
    db_config = {"uri": "sqlite://", "table": "test"}

    with patch("pandas.DataFrame.to_sql") as mock_to_sql:
        load(df, tmp_path, db_config)
        mock_to_sql.assert_called_once()


def test_end_to_end_pipeline(tmp_path, config):
    # 1. Create input CSV
    csv = tmp_path / "input.csv"
    csv.write_text(
        "tpep_pickup_datetime,tpep_dropoff_datetime,trip_distance,fare_amount\n"
        "2020-01-01 10:00,2020-01-01 10:10,1.0,10\n"
    )

    # 2. Extract
    df = extract(str(csv))

    # 3. Transform
    df = transform(df, config)

    # 4. Validate
    validate(df, config)

    # 5. Load
    out_dir = tmp_path / "out"
    load(df, out_dir, None)

    assert (out_dir / "cleaned_output.csv").exists()
