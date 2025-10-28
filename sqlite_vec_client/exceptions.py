"""Custom exception classes for sqlite-vec-client."""


class VecClientError(Exception):
    """Base exception for all sqlite-vec-client errors."""


class ValidationError(VecClientError):
    """Raised when input validation fails."""


class TableNameError(ValidationError):
    """Raised when table name is invalid."""


class TableNotFoundError(VecClientError):
    """Raised when a table does not exist."""


class ConnectionError(VecClientError):
    """Raised when database connection fails."""


class DimensionMismatchError(VecClientError):
    """Raised when embedding dimensions don't match."""
