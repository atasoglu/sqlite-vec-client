# Contributing to sqlite-vec-client

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Be respectful, constructive, and professional in all interactions.

## Getting Started

### Prerequisites

- Python 3.9+
- SQLite 3.41+
- Git

### Setup Development Environment

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/sqlite-vec-client.git
cd sqlite-vec-client
```

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

3. Install pre-commit hooks:
```bash
pre-commit install
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Write clean, readable code
- Follow existing code style
- Add tests for new features
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=sqlite_vec_client --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

### 4. Code Quality Checks

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy sqlite_vec_client/

# Run all checks
ruff check . && ruff format . && mypy sqlite_vec_client/ && pytest
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
# or
git commit -m "fix: resolve bug"
```

**Commit message format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin your-branch-name
```

Then create a pull request on GitHub.

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Code is formatted (ruff format)
- [ ] No linting errors (ruff check)
- [ ] Type checking passes (mypy)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if applicable)

### PR Description

Include:
- What changes were made
- Why the changes were needed
- How to test the changes
- Related issue numbers (if any)

## Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names: `test_<function>_<scenario>_<expected_result>`
- Use pytest fixtures from `conftest.py`
- Mark tests appropriately: `@pytest.mark.unit` or `@pytest.mark.integration`

### Test Coverage

- Aim for 80%+ coverage
- Test edge cases and error conditions
- Include security tests for user inputs

## Code Style

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names

### Documentation Style

- Docstrings for all public functions/classes
- Use Google-style docstrings
- Include examples in docstrings when helpful

Example:
```python
def add(self, texts: list[str], embeddings: list[list[float]]) -> list[int]:
    """Add texts with embeddings to the database.

    Args:
        texts: List of text strings to store.
        embeddings: List of embedding vectors (one per text).

    Returns:
        List of rowids for the inserted records.

    Raises:
        VecClientError: If insertion fails.
    """
```

## Reporting Issues

### Bug Reports

Include:
- Python version
- SQLite version
- sqlite-vec version
- Minimal code to reproduce
- Expected vs actual behavior
- Error messages/stack traces

### Feature Requests

Include:
- Use case description
- Proposed API (if applicable)
- Why existing features don't solve the problem

## Project Structure

```
sqlite-vec-client/
├── sqlite_vec_client/    # Main package
│   ├── __init__.py       # Public API
│   ├── base.py           # SQLiteVecClient class
│   ├── exceptions.py     # Custom exceptions
│   ├── types.py          # Type definitions
│   ├── utils.py          # Utility functions
│   └── validation.py     # Input validation
├── tests/                # Test suite
├── examples/             # Usage examples
└── docs/                 # Documentation (future)
```

## Areas for Contribution

Check the [TODO](TODO) file for tasks. Good starting points:

- Documentation improvements
- Additional examples
- Test coverage improvements
- Bug fixes
- Performance optimizations

## Questions?

- Open an issue for questions
- Check existing issues and PRs first
- Be patient and respectful

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
