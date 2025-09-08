"""Type aliases used across the sqlite-vec client package."""

from typing import List, Dict, Any, Tuple, TypeAlias

Text: TypeAlias = str
Rowid: TypeAlias = int
Distance: TypeAlias = float
Metadata: TypeAlias = Dict[str, Any]
Embeddings: TypeAlias = List[float]
Rowids: TypeAlias = List[Rowid]
Result: TypeAlias = Tuple[Rowid, Text, Metadata, Embeddings]
SimilaritySearchResult: TypeAlias = Tuple[Rowid, Text, Distance]
