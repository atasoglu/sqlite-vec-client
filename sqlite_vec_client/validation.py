"""Input validation utilities for sqlite-vec-client."""

from __future__ import annotations

import re

from .exceptions import DimensionMismatchError, TableNameError, ValidationError

_TABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def validate_table_name(table: str) -> None:
    """Validate table name contains only alphanumeric characters and underscores.

    Args:
        table: Table name to validate

    Raises:
        TableNameError: If table name is invalid
    """
    if not table:
        raise TableNameError("Table name cannot be empty")
    if not _TABLE_NAME_PATTERN.match(table):
        raise TableNameError(
            f"Invalid table name '{table}'. Must start with letter or underscore "
            "and contain only alphanumeric characters and underscores"
        )


def validate_dimension(dim: int) -> None:
    """Validate embedding dimension is positive.

    Args:
        dim: Embedding dimension

    Raises:
        ValidationError: If dimension is invalid
    """
    if not isinstance(dim, int) or dim <= 0:
        raise ValidationError(f"Dimension must be a positive integer, got {dim}")


def validate_top_k(top_k: int) -> None:
    """Validate top_k parameter is positive.

    Args:
        top_k: Number of results to return

    Raises:
        ValidationError: If top_k is invalid
    """
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValidationError(f"top_k must be a positive integer, got {top_k}")


def validate_limit(limit: int) -> None:
    """Validate limit parameter is positive.

    Args:
        limit: Maximum number of results

    Raises:
        ValidationError: If limit is invalid
    """
    if not isinstance(limit, int) or limit <= 0:
        raise ValidationError(f"limit must be a positive integer, got {limit}")


def validate_offset(offset: int) -> None:
    """Validate offset parameter is non-negative.

    Args:
        offset: Number of results to skip

    Raises:
        ValidationError: If offset is invalid
    """
    if not isinstance(offset, int) or offset < 0:
        raise ValidationError(f"offset must be a non-negative integer, got {offset}")


def validate_embeddings_match(
    texts: list[str], embeddings: list[list[float]], metadata: list[dict] | None = None
) -> None:
    """Validate that texts, embeddings, and metadata lists have matching lengths.

    Args:
        texts: List of text strings
        embeddings: List of embedding vectors
        metadata: Optional list of metadata dicts

    Raises:
        ValidationError: If list lengths don't match
    """
    if len(texts) != len(embeddings):
        raise ValidationError(
            f"Number of texts ({len(texts)}) must match "
            f"number of embeddings ({len(embeddings)})"
        )
    if metadata is not None and len(texts) != len(metadata):
        raise ValidationError(
            f"Number of texts ({len(texts)}) must match "
            f"number of metadata ({len(metadata)})"
        )


def validate_embedding_dimension(embedding: list[float], expected_dim: int) -> None:
    """Validate embedding has expected dimension.

    Args:
        embedding: Embedding vector
        expected_dim: Expected dimension

    Raises:
        DimensionMismatchError: If dimensions don't match
    """
    if len(embedding) != expected_dim:
        raise DimensionMismatchError(
            f"Embedding dimension {len(embedding)} does not match "
            f"expected {expected_dim}"
        )
