"""Configuration loader for benchmarks."""

import os
from typing import Any, Optional

import yaml  # type: ignore[import-untyped]


def load_config(config_path: Optional[str] = None) -> dict[str, Any]:
    """Load benchmark configuration from YAML file."""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

    with open(config_path) as f:
        result: dict[str, Any] = yaml.safe_load(f)
        return result
