# Testing Guide

This document provides comprehensive information about testing sqlite-vec-client.

## Test Structure

```
tests/
├── __init__.py           # Test package initialization
├── conftest.py           # Pytest fixtures and configuration
├── test_utils.py         # Unit tests for utility functions
├── test_validation.py    # Unit tests for validation functions
├── test_security.py      # Security tests (SQL injection, validation)
└── test_client.py        # Integration tests for SQLiteVecClient
```

## Test Categories

### Unit Tests
Tests for individual functions and modules in isolation.

**Markers:** `@pytest.mark.unit`

**Files:**
- `test_utils.py` - Tests for serialization/deserialization functions
- `test_validation.py` - Tests for input validation functions
- `test_security.py` - Security tests for SQL injection prevention and input validation

**Run unit tests only:**
```bash
pytest -m unit
```

### Integration Tests
Tests for complete workflows and client operations.

**Markers:** `@pytest.mark.integration`

**Files:**
- `test_client.py` - Tests for SQLiteVecClient methods

**Run integration tests only:**
```bash
pytest -m integration
```

## Fixtures

Common fixtures available in `conftest.py`:

- **temp_db**: Provides a temporary database file path
- **client**: Provides a SQLiteVecClient instance with temp database
- **client_with_table**: Provides a client with table already created (dim=3)
- **sample_embeddings**: 3D sample embeddings for testing
- **sample_texts**: Sample text strings
- **sample_metadata**: Sample metadata dictionaries

**Example usage:**
```python
def test_example(client_with_table, sample_texts, sample_embeddings):
    rowids = client_with_table.add(texts=sample_texts, embeddings=sample_embeddings)
    assert len(rowids) == 3
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_client.py

# Run specific test class
pytest tests/test_client.py::TestAddRecords

# Run specific test method
pytest tests/test_client.py::TestAddRecords::test_add_single_record
```

### Coverage Reports

```bash
# Run with coverage (terminal output)
pytest --cov=sqlite_vec_client

# Generate HTML coverage report
pytest --cov=sqlite_vec_client --cov-report=html

# Generate XML coverage report (for CI)
pytest --cov=sqlite_vec_client --cov-report=xml

# Show missing lines
pytest --cov=sqlite_vec_client --cov-report=term-missing
```

View HTML coverage report:
```bash
# Open htmlcov/index.html in your browser
```

### Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run slow tests
pytest -m slow

# Exclude slow tests
pytest -m "not slow"
```

## Writing Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test

```python
import pytest
from sqlite_vec_client import SQLiteVecClient

@pytest.mark.integration
class TestMyFeature:
    """Tests for my feature."""

    def test_basic_functionality(self, client_with_table):
        """Test basic functionality."""
        # Arrange
        texts = ["test"]
        embeddings = [[1.0, 2.0, 3.0]]

        # Act
        rowids = client_with_table.add(texts=texts, embeddings=embeddings)

        # Assert
        assert len(rowids) == 1
        assert client_with_table.count() == 1
```

### Testing Exceptions

```python
def test_invalid_input(self, client):
    """Test that invalid input raises error."""
    with pytest.raises(ValidationError, match="positive integer"):
        client.create_table(dim=0)
```

## Coverage Goals

- **Target:** 80%+ overall coverage
- **Current:** 91% coverage
- **Critical paths:** 100% coverage for validation and security functions

## Continuous Integration

Tests are automatically run on:
- Every commit (via pre-commit hooks)
- Pull requests (via GitHub Actions)
- Before releases

## Troubleshooting

### Common Issues

**Issue:** Tests fail with "no such table" error
```
Solution: Ensure client_with_table fixture is used for tests requiring a table
```

**Issue:** Coverage report not generated
```
Solution: Install pytest-cov: pip install pytest-cov
```

**Issue:** Tests hang or timeout
```
Solution: Check for unclosed database connections, use fixtures properly
```

## Best Practices

1. **Use fixtures** for common setup/teardown
2. **Test one thing** per test function
3. **Use descriptive names** for test functions
4. **Add docstrings** to explain what is being tested
5. **Test edge cases** (empty lists, None values, invalid inputs)
6. **Clean up resources** (fixtures handle this automatically)
7. **Mock external dependencies** when appropriate

## Performance Testing

For performance-critical operations, use the `@pytest.mark.slow` marker:

```python
@pytest.mark.slow
def test_large_batch_insert(client_with_table):
    """Test inserting 10,000 records."""
    texts = [f"text_{i}" for i in range(10000)]
    embeddings = [[0.1, 0.2, 0.3] for _ in range(10000)]
    rowids = client_with_table.add(texts=texts, embeddings=embeddings)
    assert len(rowids) == 10000
```

Run without slow tests:
```bash
pytest -m "not slow"
```
