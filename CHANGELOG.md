# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-01-28

### Added
- Enhanced GitHub release workflow with improved changelog extraction
- Better error handling in CI/CD pipeline

### Fixed
- Changelog parsing in release notes generation

## [0.2.1] - 2025-01-27

### Fixed
- PyPI publishing workflow with tag-based releases
- Changelog extraction in GitHub releases

## [0.2.0] - 2025-01-27

### Added
- `update_many()` - Bulk update multiple records in a single transaction
- `get_all()` - Memory-efficient generator for iterating over all records
- `transaction()` - Context manager for atomic multi-operation transactions
- Comprehensive tests for bulk operations (91%+ coverage)
- Updated batch_operations.py example with new features
- CONTRIBUTING.md with contribution guidelines
- CHANGELOG.md for tracking changes
- Python logging module integration with configurable log levels
- Complete CI/CD pipeline with GitHub Actions
- Pre-commit hooks and code quality tools (ruff, mypy)

### Security
- SQL injection prevention with table name validation
- Input validation for all parameters
- Custom exception classes for better error handling

## [0.1.0] - 2025-01-XX

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

## [0.0.1] - 2025-01-XX (Pre-release)

### Added
- Initial project structure
- Basic SQLiteVecClient implementation
- Proof of concept

---

## Version History

- **0.2.0** - Bulk operations, logging, security improvements, CI/CD
- **0.1.0** - First stable release with comprehensive features and testing
- **0.0.1** - Initial development version

## Upgrade Guide

### From 0.1.x to 0.2.0

No breaking changes. New features:
- Use `update_many()` for bulk updates
- Use `get_all()` for memory-efficient iteration
- Use `transaction()` context manager for atomic operations
- Configure logging via environment variable or programmatically

### From 0.0.x to 0.1.0

No breaking changes. This is the first stable release.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Links

- [GitHub Repository](https://github.com/atasoglu/sqlite-vec-client)
- [PyPI Package](https://pypi.org/project/sqlite-vec-client/)
- [Issue Tracker](https://github.com/atasoglu/sqlite-vec-client/issues)
