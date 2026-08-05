from collections.abc import Mapping
from typing import Any

import yaml


def load_config(path: str) -> Mapping[str, Any]:
    """Load and parse YAML configuration file.

    Args:
        path: The file path to the YAML configuration.

    Returns:
        A mapping containing the configuration parameters.
    """
    with open(path, "r") as f:
        return yaml.safe_load(f)
