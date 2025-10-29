"""Utilities for serializing and deserializing float32 embedding arrays."""

import json
import struct
from typing import Any

from .types import Embeddings


def serialize_f32(embeddings: Embeddings) -> bytes:
    """Serialize a list of float32 values into a packed bytes blob."""
    return struct.pack(f"{len(embeddings)}f", *embeddings)


def deserialize_f32(blob: bytes) -> Embeddings:
    """Deserialize a bytes blob of float32 values back into a list of floats."""
    return list(struct.unpack(f"{len(blob) // 4}f", blob))


def build_metadata_where_clause(filters: dict[str, Any]) -> tuple[str, list[Any]]:
    """Build SQL WHERE clause for metadata filtering using JSON_EXTRACT.

    Args:
        filters: Dictionary of metadata key-value pairs to filter by

    Returns:
        Tuple of (sql_fragment, params) for safe parameterization
    """
    conditions = []
    params: list[Any] = []
    for key, value in filters.items():
        json_path = f"$.{key}"
        if value is None:
            conditions.append("json_extract(metadata, ?) IS NULL")
            params.append(json_path)
        elif isinstance(value, bool):
            # Boolean: compare as JSON since SQLite doesn't have native bool
            conditions.append("json_extract(metadata, ?) = json(?)")
            params.append(json_path)
            params.append(json.dumps(value))
        elif isinstance(value, (int, float)):
            # Numbers: cast json_extract result to numeric for comparison
            conditions.append("CAST(json_extract(metadata, ?) AS REAL) = ?")
            params.append(json_path)
            params.append(float(value))
        else:
            # Strings and other types
            conditions.append("json_extract(metadata, ?) = ?")
            params.append(json_path)
            params.append(value)
    return " AND ".join(conditions), params
