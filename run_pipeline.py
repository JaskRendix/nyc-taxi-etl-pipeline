import logging

from pipeline.config import load_config
from pipeline.extract import extract
from pipeline.load import load
from pipeline.logging_config import setup_logging
from pipeline.transform import transform
from pipeline.validate import validate


def main():
    setup_logging()
    logging.info("Starting NYC Taxi ETL Pipeline")

    config = load_config("config.yaml")
    logging.info(f"Loaded config: {config}")

    df = extract(config["input_path"])
    logging.info(f"Extracted {len(df)} rows")

    df = transform(df, config)
    logging.info("Transformation complete")

    validate(df, config)
    logging.info("Validation complete")

    load(df, config["output_path"], config.get("database"))
    logging.info("Load complete")


if __name__ == "__main__":
    main()
