++ docs/api.md
# API Reference

The `sqlite_vec_client` package exposes a single high-level class and a few helpers.
This page captures the behaviour most consumers rely on.

## sqlite_vec_client.SQLiteVecClient

```python
from sqlite_vec_client import SQLiteVecClient
```

### Constructor

`SQLiteVecClient(table: str, db_path: str | None = None, pool: ConnectionPool | None = None)`

- Validates table name and establishes a connection (or borrows from the supplied pool).
- Loads the `sqlite-vec` extension and configures pragmas for performance.

### create_table

`create_table(dim: int, distance: Literal["L1", "L2", "cosine"] = "cosine") -> None`

Creates the base table, vector index, and triggers that keep embeddings in sync.

### add

`add(texts: list[str], embeddings: list[list[float]], metadata: list[dict] | None = None) -> list[int]`

- Validates that all embeddings match the configured dimension.
- Serialises metadata and embeddings and returns the new rowids.

### similarity_search / similarity_search_with_filter

- Both methods require embeddings that match the table dimension.
- Filtering variant accepts the same metadata constraints as `filter_by_metadata`.

### backup / restore

High-level helpers that wrap JSONL/CSV export/import:

```python
client.backup("backup.jsonl")
client.restore("backup.jsonl")

client.backup("backup.csv", format="csv", include_embeddings=True)
client.restore("backup.csv", format="csv", skip_duplicates=True)
```

### Transactions

`with client.transaction(): ...` wraps operations in a BEGIN/COMMIT pair and rolls back on error.

### Connection Management

- `client.close()` returns the connection to the pool (if configured) or closes it outright.
- Connections emit debug logs to help trace lifecycle events.

## Exceptions

- `VecClientError` — base class for client-specific errors.
- `ValidationError` — invalid user input.
- `TableNotFoundError` — operations attempted before `create_table`.
- `DimensionMismatchError` — embeddings do not match the table dimension.

## Utilities

- `serialize_f32` / `deserialize_f32` convert embeddings to/from blobs.
- Metadata helpers build safe JSON filter clauses.

Refer to `sqlite_vec_client/utils.py` for implementation details.
