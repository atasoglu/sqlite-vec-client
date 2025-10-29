# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.1] - 2025-01-31

### Changed
- Moved table name validation from `__init__()` to `create_table()` method
- Table name is now validated when creating the table schema, not during client initialization

### Improved
- More flexible client initialization - validation happens at table creation time

## [2.1.0] - 2025-01-31

### Added
- Connection pooling support via `ConnectionPool` class
- Thread-safe connection reuse for concurrent access scenarios
- Optional `pool` parameter in `SQLiteVecClient` constructor
- `examples/connection_pool_example.py` demonstrating pooled connections
- Comprehensive tests for connection pooling in `tests/test_pool.py`

### Improved
- Better resource management for multi-threaded applications
- Connection reuse reduces overhead in high-concurrency scenarios
- Backward compatible - pooling is optional

## [2.0.0] - 2025-01-30

### Changed
- **BREAKING:** Simplified `update_many()` - removed complex grouping logic (58% code reduction)
- **BREAKING:** Renamed `get_by_id()` → `get()` for cleaner API
- **BREAKING:** Renamed `delete_by_id()` → `delete()` for cleaner API

### Removed
- **BREAKING:** Removed `get_by_text()` - use SQL queries or `get_all()` with filtering
- **BREAKING:** Removed `get_by_metadata()` - use SQL queries or `get_all()` with filtering
- **BREAKING:** Removed `list_results()` - use `get_all()` generator instead

### Added
- Kept `count()` method for convenience (user request)

### Improved
- 28% smaller codebase (650 → 467 lines)
- 15% fewer methods (20 → 17)
- Test coverage increased 89% → 92%
- Cleaner, more intuitive API
- Better code maintainability
- All core CRUD and bulk operations preserved

## [1.2.0] - 2025-01-29

### Added
- Benchmarks module with comprehensive performance testing for CRUD operations
- Configurable benchmark suite via `benchmarks/config.yaml`
- Support for testing with different dataset sizes (100, 1K, 10K, 50K records)
- Benchmark operations: add, get_many, similarity_search, update_many, get_all, delete_many

### Fixed
- Fixed `delete_many()` to handle large rowid lists by batching into chunks of 500 to avoid SQLite's "too many SQL variables" error

## [1.0.1] - 2025-01-29

### Changed
- Patch release

## [1.0.0] - 2025-10-28

### Added
- `SQLiteVecClient` class for CRUD and similarity search operations
- `create_table()` - Initialize schema with configurable dimensions and distance metrics
- `add()` - Insert texts with embeddings
- `update()` - Update existing records
- `update_many()` - Bulk update multiple records in a single transaction
- `delete()` - Remove records by rowid
- `get()` - Fetch single record by rowid
- `get_many()` - Fetch multiple records
- `get_all()` - Memory-efficient generator for iterating over all records
- `get_by_text()` - Find records by exact text match
- `get_by_metadata()` - Find records by metadata JSON match
- `list_all()` - List all records with pagination
- `similarity_search()` - Vector similarity search with configurable top_k
- `count()` - Get total record count
- `clear()` - Remove all records
- `drop_table()` - Delete table and index
- `transaction()` - Context manager for atomic multi-operation transactions
- Support for text, metadata (JSON), and float32 embeddings
- Automatic synchronization between base table and vec0 index via triggers
- Context manager support for automatic connection cleanup
- Distance metrics: cosine, L2, L1
- Python logging module integration with configurable log levels
- Type hints and dataclasses for typed results
- Comprehensive test suite with 91%+ coverage
- Complete CI/CD pipeline with GitHub Actions
- Enhanced GitHub release workflow with improved changelog extraction
- Better error handling in CI/CD pipeline
- Pre-commit hooks and code quality tools (ruff, mypy)
- CONTRIBUTING.md with contribution guidelines
- CHANGELOG.md for tracking changes
- TESTING.md with testing documentation
- SECURITY_IMPROVEMENTS.md documenting security enhancements
- Multiple examples in examples/ directory
- Updated batch_operations.py example with new features
- Comprehensive README with quick start guide

### Security
- SQL injection prevention with table name validation
- Input validation for all parameters
- Custom exception classes for better error handling

### Fixed
- PyPI publishing workflow with tag-based releases
- Changelog extraction in GitHub releases
- Changelog parsing in release notes generation

## [0.1.0] - 2025-09-08

### Added
- Initial release of sqlite-vec-client
- `SQLiteVecClient` class for CRUD and similarity search operations
- Support for text, metadata (JSON), and float32 embeddings
- Automatic synchronization between base table and vec0 index via triggers
- Context manager support for automatic connection cleanup
- Comprehensive test suite with 91%+ coverage
- Security features: SQL injection prevention, input validation
- Custom exception classes for better error handling
- Type hints and dataclasses for typed results
- Examples demonstrating various use cases
- Development tooling: ruff, mypy, pre-commit hooks

### Core Features
- `create_table()` - Initialize schema with configurable dimensions and distance metrics
- `add()` - Insert texts with embeddings
- `update()` - Update existing records
- `delete()` - Remove records by rowid
- `get()` - Fetch single record by rowid
- `get_many()` - Fetch multiple records
- `get_by_text()` - Find records by exact text match
- `get_by_metadata()` - Find records by metadata JSON match
- `list_all()` - List all records with pagination
- `similarity_search()` - Vector similarity search with configurable top_k
- `count()` - Get total record count
- `clear()` - Remove all records
- `drop_table()` - Delete table and index

### Distance Metrics
- Cosine similarity (`cosine`)
- L2 distance (`l2`)
- L1 distance (`l1`)

### Documentation
- Comprehensive README with quick start guide
- TESTING.md with testing documentation
- SECURITY_IMPROVEMENTS.md documenting security enhancements
- Multiple examples in `examples/` directory

### Dependencies
- Python 3.9+
- SQLite 3.41+
- sqlite-vec 0.1.6+

---

## Version History

- **2.0.0** - Major refactor: simplified API, removed niche methods, cleaner naming
- **1.2.0** - Added benchmarks module
- **1.0.0** - First stable release
- **0.1.0** - Initial release

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Links

- [GitHub Repository](https://github.com/atasoglu/sqlite-vec-client)
- [PyPI Package](https://pypi.org/project/sqlite-vec-client/)
- [Issue Tracker](https://github.com/atasoglu/sqlite-vec-client/issues)
