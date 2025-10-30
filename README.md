# sqlite-vec-client

[![PyPI version](https://img.shields.io/pypi/v/sqlite-vec-client)](https://pypi.org/project/sqlite-vec-client/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/atasoglu/sqlite-vec-client/actions/workflows/test.yml/badge.svg)](https://github.com/atasoglu/sqlite-vec-client/actions/workflows/test.yml)

A lightweight Python client around [sqlite-vec](https://github.com/asg017/sqlite-vec) that lets you store texts, JSON metadata, and float32 embeddings in SQLite and run fast similarity search.

## Features
- **Simple API**: One class, `SQLiteVecClient`, for CRUD and search.
- **Vector index via sqlite-vec**: Uses a `vec0` virtual table under the hood.
- **Automatic sync**: Triggers keep the base table and vector index aligned.
- **Typed results**: Clear return types for results and searches.
- **Filtering helpers**: Fetch by `rowid`, `text`, or `metadata`.
- **Pagination & sorting**: List records with `limit`, `offset`, and order.
- **Bulk operations**: Efficient `update_many()`, `get_all()` generator, and transaction support.

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

## Export/Import

Export and import data in JSON or CSV formats for backups, migrations, and data sharing:

```python
# Export to JSON (includes embeddings)
count = client.export_to_json("backup.jsonl")

# Export to CSV (human-readable, optional embeddings)
count = client.export_to_csv("data.csv", include_embeddings=False)

# Export filtered data
count = client.export_to_json(
    "important.jsonl",
    filters={"priority": "high"}
)

# Import from JSON
count = client.import_from_json("backup.jsonl")

# Import from CSV
count = client.import_from_csv("data.csv")

# Backup and restore workflow
client.export_to_json("backup.jsonl")
# ... data loss ...
client.import_from_json("backup.jsonl")
```

See [examples/export_import_example.py](examples/export_import_example.py) for more examples.

## Metadata Filtering

Efficiently filter records by metadata fields using SQLite's JSON functions:

```python
# Filter by single field
results = client.filter_by_metadata({"category": "python"})

# Filter by multiple fields
results = client.filter_by_metadata({"category": "python", "year": 2024})

# Nested JSON paths
results = client.filter_by_metadata({"author.name": "Alice"})

# Count matching records
count = client.count_by_metadata({"category": "python"})

# Combined similarity search + metadata filtering
hits = client.similarity_search_with_filter(
    embedding=query_vector,
    filters={"category": "python"},
    top_k=5
)

# Pagination
results = client.filter_by_metadata(
    {"category": "python"},
    limit=10,
    offset=0
)
```

See [examples/metadata_filtering.py](examples/metadata_filtering.py) and [examples/advanced_metadata_queries.py](examples/advanced_metadata_queries.py) for more examples.

## Bulk Operations

The client provides optimized methods for bulk operations:

```python
# Bulk update multiple records
updates = [
    (rowid1, "new text", {"key": "value"}, None),
    (rowid2, None, {"updated": True}, new_embedding),
]
count = client.update_many(updates)

# Memory-efficient iteration over all records
for rowid, text, metadata, embedding in client.get_all(batch_size=100):
    process(text)

# Atomic transactions
with client.transaction():
    client.add(texts, embeddings)
    client.update_many(updates)
    client.delete_many(old_ids)
```

See [examples/batch_operations.py](examples/batch_operations.py) for more examples.

## How it works
`SQLiteVecClient` stores data in `{table}` and mirrors embeddings in `{table}_vec` (a `vec0` virtual table). SQLite triggers keep both in sync when rows are inserted, updated, or deleted. Embeddings are serialized as packed float32 bytes for compact storage.

## Logging

The library includes built-in logging support using Python's standard logging module. By default, logging is set to WARNING level.

**Configure log level via environment variable:**
```bash
export SQLITE_VEC_CLIENT_LOG_LEVEL=DEBUG  # Linux/macOS
set SQLITE_VEC_CLIENT_LOG_LEVEL=DEBUG     # Windows
```

**Or programmatically:**
```python
import logging
from sqlite_vec_client import get_logger

logger = get_logger()
logger.setLevel(logging.DEBUG)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Available log levels:**
- `DEBUG`: Detailed information for diagnosing issues
- `INFO`: General informational messages about operations
- `WARNING`: Warning messages (default)
- `ERROR`: Error messages
- `CRITICAL`: Critical error messages

See [examples/logging_example.py](examples/logging_example.py) for a complete example.

## Testing

The project has comprehensive test coverage (91%+) with 75 tests covering:
- Unit tests for utilities and validation
- Integration tests for all client operations
- Security tests for SQL injection prevention
- Edge cases and error handling

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Development

### Setup

Install development dependencies:
```bash
pip install -r requirements-dev.txt
pre-commit install
```

### Testing

The project uses pytest with comprehensive test coverage (89%+).

**Run all tests:**
```bash
pytest
```

**Run with verbose output:**
```bash
pytest -v
```

**Run specific test categories:**
```bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
```

**Run with coverage report:**
```bash
pytest --cov=sqlite_vec_client --cov-report=html
```

**Run specific test file:**
```bash
pytest tests/test_client.py
pytest tests/test_validation.py
pytest tests/test_security.py
pytest tests/test_utils.py
```

### Code Quality

**Format code:**
```bash
ruff format .
```

**Lint code:**
```bash
ruff check .
```

**Type checking:**
```bash
mypy sqlite_vec_client/
```

**Run all quality checks:**
```bash
ruff check . && ruff format . && mypy sqlite_vec_client/ && pytest
```

### Benchmarks

**Run benchmarks:**
```bash
python -m benchmarks
```

**Configure benchmarks:**
Edit [benchmarks/config.yaml](benchmarks/config.yaml) to customize:
- Dataset sizes (default: 100, 1000, 10000, 50000)
- Embedding dimension (default: 384)
- Distance metric (default: cosine)
- Database modes (file, memory)
- Similarity search iterations and top-k values

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [TESTING.md](TESTING.md) - Testing documentation
- [Examples](examples/) - Usage examples
  - [basic_usage.py](examples/basic_usage.py) - Basic CRUD operations
  - [metadata_filtering.py](examples/metadata_filtering.py) - Metadata filtering and queries
  - [advanced_metadata_queries.py](examples/advanced_metadata_queries.py) - Advanced metadata filtering with nested paths
  - [export_import_example.py](examples/export_import_example.py) - Export/import data in JSON and CSV formats
  - [transaction_example.py](examples/transaction_example.py) - Transaction management with all CRUD operations
  - [batch_operations.py](examples/batch_operations.py) - Bulk operations
  - [logging_example.py](examples/logging_example.py) - Logging configuration
- [Benchmarks](benchmarks/) - Performance benchmarks

## Contributing

Contributions are very welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT - See [LICENSE](LICENSE) for details.
