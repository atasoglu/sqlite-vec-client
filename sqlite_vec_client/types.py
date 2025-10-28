"""Type aliases used across the sqlite-vec client package."""

from typing import Any

from typing_extensions import TypeAlias

Text: TypeAlias = str
Rowid: TypeAlias = int
Distance: TypeAlias = float
Metadata: TypeAlias = dict[str, Any]
Embeddings: TypeAlias = list[float]
Rowids: TypeAlias = list[Rowid]
Result: TypeAlias = tuple[Rowid, Text, Metadata, Embeddings]
SimilaritySearchResult: TypeAlias = tuple[Rowid, Text, Distance]
