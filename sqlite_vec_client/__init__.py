"""Public package API for the sqlite-vec client.

Exposes `SQLiteVecClient` as the primary entry point.
"""

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
from .pool import ConnectionPool

__all__ = [
    "SQLiteVecClient",
    "ConnectionPool",
    "VecClientError",
    "ValidationError",
    "TableNameError",
    "TableNotFoundError",
    "ConnectionError",
    "DimensionMismatchError",
    "get_logger",
]
