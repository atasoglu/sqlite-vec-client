"""Logging configuration for sqlite-vec-client."""

import logging
import os

# Get log level from environment variable, default to WARNING
LOG_LEVEL = os.environ.get("SQLITE_VEC_CLIENT_LOG_LEVEL", "WARNING").upper()

# Create logger
logger = logging.getLogger("sqlite_vec_client")
logger.setLevel(LOG_LEVEL)

# Only add handler if none exists (avoid duplicate handlers)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_logger() -> logging.Logger:
    """Get the configured logger instance.

    Returns:
        Logger instance for sqlite-vec-client
    """
    return logger
