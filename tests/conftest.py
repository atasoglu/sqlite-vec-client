"""Pytest fixtures and configuration for sqlite-vec-client tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from sqlite_vec_client import SQLiteVecClient


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Provide a temporary database file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield str(Path(tmpdir) / "test.db")


@pytest.fixture
def client(temp_db: str) -> Generator[SQLiteVecClient, None, None]:
    """Provide a SQLiteVecClient instance with a temporary database."""
    client = SQLiteVecClient(table="test_table", db_path=temp_db)
    yield client
    client.close()


@pytest.fixture
def client_with_table(client: SQLiteVecClient) -> SQLiteVecClient:
    """Provide a client with table already created."""
    client.create_table(dim=3, distance="cosine")
    return client


@pytest.fixture
def sample_embeddings() -> list[list[float]]:
    """Provide sample 3D embeddings for testing."""
    return [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9],
    ]


@pytest.fixture
def sample_texts() -> list[str]:
    """Provide sample texts for testing."""
    return ["hello world", "lorem ipsum", "vector database"]


@pytest.fixture
def sample_metadata() -> list[dict]:
    """Provide sample metadata for testing."""
    return [
        {"category": "greeting", "lang": "en"},
        {"category": "placeholder", "lang": "la"},
        {"category": "tech", "lang": "en"},
    ]
