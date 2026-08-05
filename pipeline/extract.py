from pathlib import Path

import pandas as pd


def extract(path: str | Path) -> pd.DataFrame:
    """Extract raw taxi trip data from a CSV or Parquet file.

    Args:
        path: The file path to the input data source.

    Returns:
        A pandas DataFrame containing the raw trip data.

    Raises:
        ValueError: If the file extension is not supported.
    """
    file_path = Path(path)

    if file_path.suffix == ".csv":
        return pd.read_csv(
            file_path, parse_dates=["tpep_pickup_datetime", "tpep_dropoff_datetime"]
        )

    if file_path.suffix == ".parquet":
        return pd.read_parquet(file_path)

    raise ValueError(f"Unsupported file type: {file_path.suffix}")
