"""Utilities for serializing and deserializing float32 embedding arrays."""

import struct

from .types import Embeddings


def serialize_f32(embeddings: Embeddings) -> bytes:
    """Serialize a list of float32 values into a packed bytes blob."""
    return struct.pack(f"{len(embeddings)}f", *embeddings)


def deserialize_f32(blob: bytes) -> Embeddings:
    """Deserialize a bytes blob of float32 values back into a list of floats."""
    return list(struct.unpack(f"{len(blob) // 4}f", blob))
