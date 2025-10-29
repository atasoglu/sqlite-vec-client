"""Connection pooling for SQLite connections."""

from __future__ import annotations

import sqlite3
import threading
from typing import Callable

from .logger import get_logger

logger = get_logger()


class ConnectionPool:
    """Thread-local connection pool for SQLite databases.

    Note: SQLite connections are not thread-safe. This pool creates
    one connection per thread and reuses it within that thread.
    """

    def __init__(
        self,
        connection_factory: Callable[[], sqlite3.Connection],
        pool_size: int = 5,
    ) -> None:
        """Initialize connection pool.

        Args:
            connection_factory: Function that creates new connections
            pool_size: Maximum number of connections (one per thread)
        """
        if pool_size < 1:
            raise ValueError("pool_size must be at least 1")

        self._factory = connection_factory
        self._pool_size = pool_size
        self._local = threading.local()
        self._lock = threading.Lock()
        self._created = 0
        self._all_connections: list[sqlite3.Connection] = []
        logger.debug(f"Initialized connection pool with size={pool_size}")

    def get_connection(self) -> sqlite3.Connection:
        """Get a connection for the current thread.

        Returns:
            SQLite connection for this thread
        """
        if hasattr(self._local, "connection"):
            conn: sqlite3.Connection = self._local.connection
            logger.debug("Reused thread-local connection")
            return conn

        with self._lock:
            if self._created >= self._pool_size:
                raise RuntimeError(f"Connection pool exhausted (max={self._pool_size})")
            conn = self._factory()
            self._created += 1
            self._all_connections.append(conn)
            self._local.connection = conn
            logger.debug(f"Created new connection ({self._created}/{self._pool_size})")
            return conn

    def return_connection(self, conn: sqlite3.Connection) -> None:
        """Return a connection (no-op for thread-local pool).

        Args:
            conn: Connection to return (kept in thread-local storage)
        """
        logger.debug("Connection kept in thread-local storage")

    def close_all(self) -> None:
        """Close all connections in the pool."""
        logger.debug("Closing all connections in pool")
        with self._lock:
            for conn in self._all_connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
            closed = len(self._all_connections)
            self._all_connections.clear()
            self._created = 0
        logger.info(f"Closed {closed} connections from pool")
