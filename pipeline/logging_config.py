import logging


def setup_logging() -> None:
    """Configure root logger with a standard info level and timestamp format.

    Returns:
        None
    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
