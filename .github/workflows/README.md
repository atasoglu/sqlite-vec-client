# GitHub Actions Workflows

This directory contains CI/CD workflows for the sqlite-vec-client project.

## Workflows

### test.yml - Continuous Integration
Runs on every push and pull request to `main` and `develop` branches.

**What it does:**
- Tests across Python 3.9-3.13
- Tests on Ubuntu, Windows, and macOS
- Runs linting (ruff check)
- Runs format checking (ruff format)
- Runs type checking (mypy)
- Runs test suite with coverage report

### publish.yml - PyPI Publishing
Runs automatically when a GitHub release is published.

**What it does:**
- Builds the package
- Publishes to PyPI using the PYPI_API_TOKEN secret

## Setup Requirements

### For PyPI Publishing
1. Generate a PyPI API token at [pypi.org](https://pypi.org/manage/account/token/)
2. Add `PYPI_API_TOKEN` to GitHub repository secrets

## Badge URL

Add this to your README.md:

```markdown
[![CI](https://github.com/atasoglu/sqlite-vec-client/actions/workflows/test.yml/badge.svg)](https://github.com/atasoglu/sqlite-vec-client/actions/workflows/test.yml)
```
