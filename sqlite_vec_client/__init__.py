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

__all__ = [
    "SQLiteVecClient",
    "VecClientError",
    "ValidationError",
    "TableNameError",
    "TableNotFoundError",
    "ConnectionError",
    "DimensionMismatchError",
]
