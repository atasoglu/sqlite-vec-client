"""Public package API for the sqlite-vec client.

Exposes `SQLiteVecClient` as the primary entry point.
"""

__version__ = "0.2.0"

from .base import SQLiteVecClient
from .exceptions import (
    ConnectionError,
    DimensionMismatchError,
    TableNameError,
    TableNotFoundError,
    ValidationError,
    VecClientError,
)
from .logger import get_logger

__all__ = [
    "__version__",
    "SQLiteVecClient",
    "VecClientError",
    "ValidationError",
    "TableNameError",
    "TableNotFoundError",
    "ConnectionError",
    "DimensionMismatchError",
    "get_logger",
]
