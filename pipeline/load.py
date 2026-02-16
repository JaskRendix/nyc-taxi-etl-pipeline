import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine


def load(df: pd.DataFrame, output_path: str, db_config: dict = None) -> None:
    Path(output_path).mkdir(exist_ok=True)
    csv_path = Path(output_path) / "cleaned_output.csv"

    df.to_csv(csv_path, index=False)
    logging.info(f"Saved cleaned CSV to {csv_path}")

    if db_config:
        engine = create_engine(db_config["uri"])
        table = db_config["table"]

        df.to_sql(table, engine, if_exists="replace", index=False)
        logging.info(f"Loaded cleaned data into SQL table '{table}'")
