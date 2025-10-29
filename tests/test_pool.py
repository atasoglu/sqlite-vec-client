"""Tests for connection pooling."""

import sqlite3
import threading
from unittest.mock import MagicMock

import pytest

from sqlite_vec_client import ConnectionPool, SQLiteVecClient


def test_pool_initialization():
    """Test connection pool initialization."""
    factory = MagicMock(return_value=MagicMock(spec=sqlite3.Connection))
    pool = ConnectionPool(factory, pool_size=3)
    assert pool._pool_size == 3
    assert pool._created == 0


def test_pool_invalid_size():
    """Test that invalid pool size raises error."""
    factory = MagicMock()
    with pytest.raises(ValueError, match="pool_size must be at least 1"):
        ConnectionPool(factory, pool_size=0)


def test_pool_get_connection():
    """Test getting connection from pool."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    factory = MagicMock(return_value=mock_conn)
    pool = ConnectionPool(factory, pool_size=2)

    conn = pool.get_connection()
    assert conn == mock_conn
    assert pool._created == 1
    factory.assert_called_once()


def test_pool_return_connection():
    """Test returning connection to pool (thread-local reuse)."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    factory = MagicMock(return_value=mock_conn)
    pool = ConnectionPool(factory, pool_size=2)

    conn = pool.get_connection()
    pool.return_connection(conn)

    # Get again should reuse (same thread)
    conn2 = pool.get_connection()
    assert conn2 == conn
    assert pool._created == 1


def test_pool_close_all():
    """Test closing all connections in pool."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    factory = MagicMock(return_value=mock_conn)
    pool = ConnectionPool(factory, pool_size=2)

    pool.get_connection()
    pool.close_all()
    mock_conn.close.assert_called_once()


def test_client_with_pool(tmp_path):
    """Test SQLiteVecClient with connection pool."""
    db_path = str(tmp_path / "test.db")

    pool = ConnectionPool(
        lambda: SQLiteVecClient.create_connection(db_path), pool_size=2
    )

    client1 = SQLiteVecClient(table="docs", pool=pool)
    client1.create_table(dim=3)
    client1.add(["test"], [[0.1, 0.2, 0.3]])
    client1.close()

    # Reuse connection from pool
    client2 = SQLiteVecClient(table="docs", pool=pool)
    assert client2.count() == 1
    client2.close()

    pool.close_all()


def test_client_without_pool(tmp_path):
    """Test SQLiteVecClient without pool (backward compatibility)."""
    db_path = str(tmp_path / "test.db")

    client = SQLiteVecClient(table="docs", db_path=db_path)
    client.create_table(dim=3)
    client.add(["test"], [[0.1, 0.2, 0.3]])
    assert client.count() == 1
    client.close()


def test_pool_thread_safety(tmp_path):
    """Test connection pool with multiple threads."""
    db_path = str(tmp_path / "test.db")
    pool = ConnectionPool(
        lambda: SQLiteVecClient.create_connection(db_path), pool_size=5
    )

    results = []
    lock = threading.Lock()

    def worker(worker_id: int):
        try:
            client = SQLiteVecClient(table=f"t{worker_id}", pool=pool)
            client.create_table(dim=2)
            client.add([f"doc{worker_id}"], [[0.1, 0.2]])
            count = client.count()
            client.close()
            with lock:
                results.append(count)
        except Exception:
            with lock:
                results.append(None)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 5
    assert all(r == 1 for r in results)
    pool.close_all()


def test_client_requires_db_path_or_pool():
    """Test that either db_path or pool must be provided."""
    with pytest.raises(ValueError, match="Either db_path or pool must be provided"):
        SQLiteVecClient(table="docs")
