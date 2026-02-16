from pathlib import Path

import pandas as pd


def extract(path: str) -> pd.DataFrame:
    path = Path(path)

    if path.suffix == ".csv":
        return pd.read_csv(
            path, parse_dates=["tpep_pickup_datetime", "tpep_dropoff_datetime"]
        )

    if path.suffix == ".parquet":
        return pd.read_parquet(path)

    raise ValueError(f"Unsupported file type: {path.suffix}")
