import struct
from .types import Embeddings


def serialize_f32(embeddings: Embeddings) -> bytes:
    return struct.pack("%sf" % len(embeddings), *embeddings)


def deserialize_f32(blob: bytes) -> Embeddings:
    return list(struct.unpack("%sf" % (len(blob) // 4), blob))
