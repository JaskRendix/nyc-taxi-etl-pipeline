import json
import math
import pickle
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest

from pipeline.train_model import (
    METRICS_PATH,
    MODEL_PATH,
    build_feature_target,
    load_config,
    load_data_from_db,
    save_artifacts,
    train_model,
)


def metrics_equal(m1: Mapping[str, float], m2: Mapping[str, float]) -> bool:
    for key in m1:
        v1 = m1[key]
        v2 = m2[key]

        # Handle NaN explicitly
        if isinstance(v1, float) and math.isnan(v1):
            if not (isinstance(v2, float) and math.isnan(v2)):
                return False
        else:
            if v1 != v2:
                return False

    return True


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Minimal valid DataFrame for model training."""
    return pd.DataFrame(
        {
            "fare_amount": [10.0, 20.0, 30.0],
            "trip_distance": [1.0, 2.0, 3.0],
            "trip_duration": [5.0, 10.0, 15.0],
            "hour": [10, 11, 12],
            "passenger_count": [1, 2, 1],
            "distance_bucket": [0, 1, 2],
            "duration_bucket": [0, 1, 2],
            "speed_mpm": [0.2, 0.2, 0.2],
            "is_peak_hour": [0, 1, 0],
            "is_airport": [0, 0, 1],
        }
    )


@pytest.fixture
def config(tmp_path: Path) -> dict[str, Any]:
    """Fake config with DB URL."""
    cfg: dict[str, Any] = {
        "database": {"url": "sqlite://"},
        "anomaly_thresholds": {
            "short_expensive": {"duration": 5, "fare": 50},
            "long_duration": 180,
            "cheap_per_mile": 0.5,
        },
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    return cfg


def test_build_feature_target_valid(sample_df: pd.DataFrame) -> None:
    X, y = build_feature_target(sample_df)
    assert len(X) == 3
    assert len(y) == 3
    assert list(X.columns) == [
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


def test_build_feature_target_missing_columns(sample_df: pd.DataFrame) -> None:
    df = sample_df.drop(columns=["trip_distance"])
    with pytest.raises(KeyError):
        build_feature_target(df)


def test_train_model_output(sample_df: pd.DataFrame) -> None:
    X, y = build_feature_target(sample_df)
    model, metrics = train_model(X, y)

    assert hasattr(model, "predict")
    assert set(metrics.keys()) == {"mae", "rmse", "r2"}
    assert isinstance(metrics["mae"], float)
    assert isinstance(metrics["rmse"], float)
    assert isinstance(metrics["r2"], float)


def test_train_model_reproducibility(sample_df: pd.DataFrame) -> None:
    X, y = build_feature_target(sample_df)

    _, metrics1 = train_model(X, y)
    _, metrics2 = train_model(X, y)

    assert metrics_equal(metrics1, metrics2)


def test_save_artifacts(tmp_path: Path, sample_df: pd.DataFrame) -> None:
    # Redirect artifact paths
    model_path = tmp_path / "fare_model.pkl"
    metrics_path = tmp_path / "metrics.json"

    X, y = build_feature_target(sample_df)
    model, metrics = train_model(X, y)

    with patch("pipeline.train_model.MODEL_PATH", model_path), patch(
        "pipeline.train_model.METRICS_PATH", metrics_path
    ):
        save_artifacts(model, metrics)

    assert model_path.exists()
    assert metrics_path.exists()

    # Validate model file
    with model_path.open("rb") as f:
        loaded_model = pickle.load(f)
    assert hasattr(loaded_model, "predict")

    # Validate metrics JSON
    with metrics_path.open("r", encoding="utf-8") as f:
        loaded_metrics = json.load(f)

    assert metrics_equal(loaded_metrics, metrics)


def test_load_data_from_db_calls_sqlalchemy(config: dict[str, Any]) -> None:
    with patch("pipeline.train_model.create_engine") as mock_engine:
        mock_engine.return_value.connect.return_value = None
        with patch("pandas.read_sql") as mock_read:
            mock_read.return_value = pd.DataFrame({"a": [1]})
            df = load_data_from_db(config)
            assert isinstance(df, pd.DataFrame)
            mock_read.assert_called_once()


def test_main_end_to_end(tmp_path: Path, sample_df: pd.DataFrame) -> None:
    """Simulate full training pipeline without touching real DB."""
    with patch("pipeline.train_model.load_data_from_db") as mock_load:
        mock_load.return_value = sample_df

        with patch("pipeline.train_model.load_config") as mock_cfg:
            mock_cfg.return_value = {
                "database": {"url": "sqlite://"},
                "anomaly_thresholds": {},
            }

            model_path = tmp_path / "fare_model.pkl"
            metrics_path = tmp_path / "metrics.json"

            with patch("pipeline.train_model.MODEL_PATH", model_path), patch(
                "pipeline.train_model.METRICS_PATH", metrics_path
            ):
                from pipeline.train_model import main

                main()

            assert model_path.exists()
            assert metrics_path.exists()
