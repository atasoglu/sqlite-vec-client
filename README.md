# sqlite-vec-client

A tiny, lightweight Pythonic helper around [sqlite-vec](https://github.com/asg017/sqlite-vec) that lets you store texts, JSON metadata, and float32 embeddings in SQLite and run fast similarity search.

## Features
- **Simple API**: One class, `SQLiteVecClient`, for CRUD and search.
- **Vector index via sqlite-vec**: Uses a `vec0` virtual table under the hood.
- **Automatic sync**: Triggers keep the base table and vector index aligned.
- **Typed results**: Clear return types for results and searches.
- **Filtering helpers**: Fetch by `rowid`, `text`, or `metadata`.
- **Pagination & sorting**: List records with `limit`, `offset`, and order.

## Requirements
- Python 3.9+
- [SQLite version 3.41 or higher](https://alexgarcia.xyz/sqlite-vec/python.html#updated-sqlite)
- [The sqlite-vec extension](https://github.com/asg017/sqlite-vec)

## Installation
Install from PyPI:

```bash
pip install sqlite-vec-client
```

Or:

```bash
git clone https://github.com/atasoglu/sqlite-vec-client
cd sqlite-vec-client
pip install .
```

## Quick start
```python
from sqlite_vec_client import SQLiteVecClient

# Initialize a client bound to a specific table in a database file
client = SQLiteVecClient(table="documents", db_path="./example.db")

# Create schema (base table + vec index); choose embedding dimension and distance
client.create_table(dim=384, distance="cosine")

# Add some texts with embeddings (one embedding per text)
texts = ["hello world", "lorem ipsum", "vector databases"]
embs = [
    [0.1, 0.2, 0.3, *([0.0] * 381)],
    [0.05, 0.04, 0.03, *([0.0] * 381)],
    [0.2, 0.1, 0.05, *([0.0] * 381)],
]
rowids = client.add(texts=texts, embeddings=embs)

# Similarity search returns (rowid, text, distance)
query_emb = [0.1, 0.2, 0.3, *([0.0] * 381)]
hits = client.similarity_search(embedding=query_emb, top_k=3)

# Fetch full rows (rowid, text, metadata, embedding)
rows = client.get_many(rowids)

client.close()
```

## How it works
`SQLiteVecClient` stores data in `{table}` and mirrors embeddings in `{table}_vec` (a `vec0` virtual table). SQLite triggers keep both in sync when rows are inserted, updated, or deleted. Embeddings are serialized as packed float32 bytes for compact storage.

## Contributing
Contributions are very welcome—issues, ideas, and PRs help this project grow!

## License

MIT