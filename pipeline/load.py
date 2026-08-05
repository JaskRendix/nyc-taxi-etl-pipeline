import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine


def load(
    df: pd.DataFrame, output_path: str, db_config: Mapping[str, Any] | None = None
) -> None:
    """Save the cleaned DataFrame to a CSV file and optionally load it into a PostgreSQL database.

    Args:
        df: The cleaned and validated pandas DataFrame.
        output_path: The directory path where the output CSV will be saved.
        db_config: Optional mapping containing database connection URI and table name.

    Returns:
        None
    """
    Path(output_path).mkdir(parents=True, exist_ok=True)
    csv_path = Path(output_path) / "cleaned_output.csv"

    df.to_csv(csv_path, index=False)
    logging.info(f"Saved cleaned CSV to {csv_path}")

    if db_config:
        engine = create_engine(db_config["uri"])
        table: str = db_config["table"]

        df.to_sql(table, engine, if_exists="replace", index=False)
        logging.info(f"Loaded cleaned data into SQL table '{table}'")
