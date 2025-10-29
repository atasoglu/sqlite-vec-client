"""High-level client for vector search on SQLite using the sqlite-vec extension.

This module provides `SQLiteVecClient`, a thin wrapper around `sqlite3` and
`sqlite-vec` to store texts, JSON metadata, and float32 embeddings, and to run
similarity search through a virtual vector table.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from types import TracebackType
from typing import TYPE_CHECKING, Any, Literal

import sqlite_vec

from . import io as io_module
from .exceptions import ConnectionError as VecConnectionError
from .exceptions import TableNotFoundError
from .logger import get_logger
from .types import Embeddings, Metadata, Result, Rowids, SimilaritySearchResult, Text
from .utils import build_metadata_where_clause, deserialize_f32, serialize_f32
from .validation import (
    validate_dimension,
    validate_embeddings_match,
    validate_limit,
    validate_metadata_filters,
    validate_offset,
    validate_table_name,
    validate_top_k,
)

if TYPE_CHECKING:
    from .pool import ConnectionPool

logger = get_logger()


class SQLiteVecClient:
    """Manage a text+embedding table and its sqlite-vec index.

    The client maintains two tables:
    - `{table}`: base table with columns `text`, `metadata`, `text_embedding`.
    - `{table}_vec`: `vec0` virtual table mirroring embeddings for ANN search.

    It exposes CRUD helpers and `similarity_search` over embeddings.
    """

    @staticmethod
    def create_connection(db_path: str) -> sqlite3.Connection:
        """Create a SQLite connection with sqlite-vec extension loaded.

        Args:
            db_path: Path to SQLite database file

        Returns:
            SQLite connection with sqlite-vec loaded

        Raises:
            VecConnectionError: If connection or extension loading fails
        """
        try:
            logger.debug(f"Connecting to database: {db_path}")
            connection = sqlite3.connect(db_path)
            connection.row_factory = sqlite3.Row
            connection.enable_load_extension(True)
            sqlite_vec.load(connection)
            connection.enable_load_extension(False)

            # Performance optimizations
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.execute("PRAGMA cache_size=-64000")  # 64MB cache
            connection.execute("PRAGMA temp_store=MEMORY")

            logger.info(f"Successfully connected to database: {db_path}")
            return connection
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database {db_path}: {e}")
            raise VecConnectionError(f"Failed to connect to database: {e}") from e
        except Exception as e:
            logger.error(f"Failed to load sqlite-vec extension: {e}")
            raise VecConnectionError(f"Failed to load sqlite-vec extension: {e}") from e

    @staticmethod
    def rows_to_results(rows: list[sqlite3.Row]) -> list[Result]:
        """Convert `sqlite3.Row` items into `(rowid, text, metadata, embedding)`."""
        return [
            (
                row["rowid"],
                row["text"],
                json.loads(row["metadata"]),
                deserialize_f32(row["text_embedding"]),
            )
            for row in rows
        ]

    def __init__(
        self, table: str, db_path: str | None = None, pool: ConnectionPool | None = None
    ) -> None:
        """Initialize the client for a given base table and database file.

        Args:
            table: Name of the base table
            db_path: Path to SQLite database file (required if pool is None)
            pool: Optional connection pool for connection reuse

        Raises:
            VecConnectionError: If connection fails
            ValueError: If both db_path and pool are None
        """
        self.table = table
        self._in_transaction = False
        self._pool = pool
        logger.debug(f"Initializing SQLiteVecClient for table: {table}")

        if pool:
            self.connection = pool.get_connection()
            logger.debug("Using connection from pool")
        elif db_path:
            self.connection = self.create_connection(db_path)
        else:
            raise ValueError("Either db_path or pool must be provided")

    def __enter__(self) -> SQLiteVecClient:
        """Support context manager protocol and return `self`."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the connection on exit; do not suppress exceptions."""
        self.close()

    def create_table(
        self,
        dim: int,
        distance: Literal["L1", "L2", "cosine"] = "cosine",
    ) -> None:
        """Create base table, vector table, and triggers to keep them in sync.

        Args:
            dim: Embedding dimension (must be positive)
            distance: Distance metric for similarity search

        Raises:
            TableNameError: If table name is invalid
            ValidationError: If dimension is invalid
        """
        validate_table_name(self.table)
        validate_dimension(dim)
        logger.info(
            f"Creating table '{self.table}' with dim={dim}, distance={distance}"
        )
        self.connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table}
            (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                metadata BLOB,
                text_embedding BLOB
            )
            ;
            """
        )
        self.connection.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {self.table}_vec USING vec0(
                rowid INTEGER PRIMARY KEY,
                text_embedding float[{dim}] distance_metric={distance}
            )
            ;
            """
        )
        self.connection.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {self.table}_embed_text
            AFTER INSERT ON {self.table}
            BEGIN
                INSERT INTO {self.table}_vec(rowid, text_embedding)
                VALUES (new.rowid, new.text_embedding)
                ;
            END;
            """
        )
        self.connection.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {self.table}_update_text_embedding
            AFTER UPDATE OF text_embedding ON {self.table}
            BEGIN
                UPDATE {self.table}_vec
                SET text_embedding = new.text_embedding
                WHERE rowid = new.rowid
                ;
            END;
            """
        )
        self.connection.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {self.table}_delete_row
            AFTER DELETE ON {self.table}
            BEGIN
                DELETE FROM {self.table}_vec WHERE rowid = old.rowid
                ;
            END;
            """
        )
        self.connection.commit()
        logger.debug(f"Table '{self.table}' and triggers created successfully")

    def similarity_search(
        self,
        embedding: Embeddings,
        top_k: int = 5,
    ) -> list[SimilaritySearchResult]:
        """Return top-k nearest neighbors for the given embedding.

        Args:
            embedding: Query embedding vector
            top_k: Number of results to return (must be positive)

        Returns:
            List of (rowid, text, distance) tuples

        Raises:
            ValidationError: If top_k is invalid
            TableNotFoundError: If table doesn't exist
        """
        validate_top_k(top_k)
        logger.debug(f"Performing similarity search with top_k={top_k}")
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                f"""
                SELECT
                    e.rowid AS rowid,
                    text,
                    distance
                FROM {self.table} AS e
                INNER JOIN {self.table}_vec AS v on v.rowid = e.rowid
                WHERE
                    v.text_embedding MATCH ?
                    AND k = ?
                ORDER BY v.distance
                """,
                [serialize_f32(embedding), top_k],
            )
            results = cursor.fetchall()
            logger.debug(f"Similarity search returned {len(results)} results")
            return [(row["rowid"], row["text"], row["distance"]) for row in results]
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                logger.error(f"Table '{self.table}' not found during similarity search")
                raise TableNotFoundError(
                    f"Table '{self.table}' or '{self.table}_vec' does not exist. "
                    "Call create_table() first."
                ) from e
            raise

    def count(self) -> int:
        """Return the total number of rows in the base table."""
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT COUNT(1) FROM {self.table}")
        result = cursor.fetchone()
        return int(result[0]) if result else 0

    def add(
        self,
        texts: list[Text],
        embeddings: list[Embeddings],
        metadata: list[Metadata] | None = None,
    ) -> Rowids:
        """Insert texts with embeddings (and optional metadata) and return rowids.

        Args:
            texts: List of text strings
            embeddings: List of embedding vectors
            metadata: Optional list of metadata dicts

        Returns:
            List of rowids for inserted records

        Raises:
            ValidationError: If list lengths don't match
            TableNotFoundError: If table doesn't exist
        """
        validate_embeddings_match(texts, embeddings, metadata)
        logger.debug(f"Adding {len(texts)} records to table '{self.table}'")
        try:
            if metadata is None:
                metadata = [dict() for _ in texts]

            data_input = [
                (text, json.dumps(md), serialize_f32(embedding))
                for text, md, embedding in zip(texts, metadata, embeddings)
            ]

            cur = self.connection.cursor()

            # Get max rowid before insert
            max_before = cur.execute(
                f"SELECT COALESCE(MAX(rowid), 0) FROM {self.table}"
            ).fetchone()[0]

            cur.executemany(
                f"""INSERT INTO {self.table}(text, metadata, text_embedding)
                VALUES (?,?,?)""",
                data_input,
            )

            # Calculate rowids from max_before
            rowids = list(range(max_before + 1, max_before + len(texts) + 1))

            if not self._in_transaction:
                self.connection.commit()

            logger.info(f"Added {len(rowids)} records to table '{self.table}'")
            return rowids
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                logger.error(f"Table '{self.table}' not found during add operation")
                raise TableNotFoundError(
                    f"Table '{self.table}' does not exist. Call create_table() first."
                ) from e
            raise

    def get(self, rowid: int) -> Result | None:
        """Get a single record by rowid; return `None` if not found."""
        cursor = self.connection.cursor()
        cursor.execute(
            f"""
            SELECT rowid, text, metadata, text_embedding
            FROM {self.table} WHERE rowid = ?
            """,
            [rowid],
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self.rows_to_results([row])[0]

    def get_many(self, rowids: list[int]) -> list[Result]:
        """Get multiple records by rowids; returns empty list if input is empty."""
        if not rowids:
            return []
        placeholders = ",".join(["?"] * len(rowids))
        cursor = self.connection.cursor()
        cursor.execute(
            f"""SELECT rowid, text, metadata, text_embedding FROM {self.table}
            WHERE rowid IN ({placeholders})""",
            rowids,
        )
        rows = cursor.fetchall()
        return self.rows_to_results(rows)

    def get_all(self, batch_size: int = 100) -> Generator[Result, None, None]:
        """Yield all records in batches for memory-efficient iteration.

        Args:
            batch_size: Number of records to fetch per batch

        Yields:
            Individual (rowid, text, metadata, embedding) tuples
        """
        validate_limit(batch_size)
        logger.debug(f"Fetching all records with batch_size={batch_size}")
        last_rowid = 0
        cursor = self.connection.cursor()

        while True:
            cursor.execute(
                f"""
                SELECT rowid, text, metadata, text_embedding FROM {self.table}
                WHERE rowid > ?
                ORDER BY rowid ASC
                LIMIT ?
                """,
                [last_rowid, batch_size],
            )
            rows = cursor.fetchall()
            if not rows:
                break

            results = self.rows_to_results(rows)
            yield from results
            last_rowid = results[-1][0]  # Get last rowid from batch

    def update(
        self,
        rowid: int,
        *,
        text: str | None = None,
        metadata: Metadata | None = None,
        embedding: Embeddings | None = None,
    ) -> bool:
        """Update fields of a record by rowid; return True if a row changed."""
        logger.debug(f"Updating record with rowid={rowid}")
        sets = []
        params: list[Any] = []
        if text is not None:
            sets.append("text = ?")
            params.append(text)
        if metadata is not None:
            sets.append("metadata = ?")
            params.append(json.dumps(metadata))
        if embedding is not None:
            sets.append("text_embedding = ?")
            params.append(serialize_f32(embedding))

        if not sets:
            return False

        params.append(rowid)
        sql = f"UPDATE {self.table} SET " + ", ".join(sets) + " WHERE rowid = ?"
        cur = self.connection.cursor()
        cur.execute(sql, params)
        if not self._in_transaction:
            self.connection.commit()
        updated = cur.rowcount > 0
        if updated:
            logger.debug(f"Successfully updated record with rowid={rowid}")
        return updated

    def update_many(
        self,
        updates: list[tuple[int, str | None, Metadata | None, Embeddings | None]],
    ) -> int:
        """Update multiple records in a single transaction.

        Args:
            updates: List of (rowid, text, metadata, embedding) tuples.
                     Any field except rowid can be None to skip updating.

        Returns:
            Number of rows updated
        """
        if not updates:
            return 0
        logger.debug(f"Updating {len(updates)} records")

        cur = self.connection.cursor()
        updated_count = 0

        for rowid, text, metadata, embedding in updates:
            sets: list[str] = []
            params: list[Any] = []
            if text is not None:
                sets.append("text = ?")
                params.append(text)
            if metadata is not None:
                sets.append("metadata = ?")
                params.append(json.dumps(metadata))
            if embedding is not None:
                sets.append("text_embedding = ?")
                params.append(serialize_f32(embedding))

            if sets:
                params.append(rowid)
                cur.execute(
                    f"UPDATE {self.table} SET {', '.join(sets)} WHERE rowid = ?",
                    params,
                )
                updated_count += cur.rowcount

        if not self._in_transaction:
            self.connection.commit()

        logger.info(f"Updated {updated_count} records in table '{self.table}'")
        return updated_count

    def delete(self, rowid: int) -> bool:
        """Delete a single record by rowid; return True if a row was removed."""
        logger.debug(f"Deleting record with rowid={rowid}")
        cur = self.connection.cursor()
        cur.execute(f"DELETE FROM {self.table} WHERE rowid = ?", [rowid])
        if not self._in_transaction:
            self.connection.commit()
        deleted = cur.rowcount > 0
        if deleted:
            logger.debug(f"Successfully deleted record with rowid={rowid}")
        return deleted

    def delete_many(self, rowids: list[int]) -> int:
        """Delete multiple records by rowids; return number of rows removed."""
        if not rowids:
            return 0
        logger.debug(f"Deleting {len(rowids)} records")

        # SQLite has a limit on SQL variables (typically 999 or 32766)
        # Split into chunks to avoid "too many SQL variables" error
        chunk_size = 500
        cur = self.connection.cursor()
        deleted_count = 0

        for i in range(0, len(rowids), chunk_size):
            chunk = rowids[i : i + chunk_size]
            placeholders = ",".join(["?"] * len(chunk))
            cur.execute(
                f"DELETE FROM {self.table} WHERE rowid IN ({placeholders})",
                chunk,
            )
            deleted_count += cur.rowcount

        if not self._in_transaction:
            self.connection.commit()

        logger.info(f"Deleted {deleted_count} records from table '{self.table}'")
        return deleted_count

    def filter_by_metadata(
        self, filters: dict[str, Any], limit: int = 100, offset: int = 0
    ) -> list[Result]:
        """Filter records by metadata key-value pairs.

        Args:
            filters: Dictionary of metadata key-value pairs to match
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of matching (rowid, text, metadata, embedding) tuples

        Raises:
            ValidationError: If filters or pagination params are invalid
        """
        validate_metadata_filters(filters)
        validate_limit(limit)
        validate_offset(offset)
        logger.debug(f"Filtering by metadata: {filters}")

        where_clause, params = build_metadata_where_clause(filters)
        cursor = self.connection.cursor()
        cursor.execute(
            f"""
            SELECT rowid, text, metadata, text_embedding
            FROM {self.table}
            WHERE {where_clause}
            ORDER BY rowid ASC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )
        rows = cursor.fetchall()
        logger.debug(f"Found {len(rows)} records matching filters")
        return self.rows_to_results(rows)

    def count_by_metadata(self, filters: dict[str, Any]) -> int:
        """Count records matching metadata filters.

        Args:
            filters: Dictionary of metadata key-value pairs to match

        Returns:
            Number of matching records

        Raises:
            ValidationError: If filters are invalid
        """
        validate_metadata_filters(filters)
        where_clause, params = build_metadata_where_clause(filters)
        cursor = self.connection.cursor()
        cursor.execute(
            f"SELECT COUNT(1) FROM {self.table} WHERE {where_clause}", params
        )
        result = cursor.fetchone()
        return int(result[0]) if result else 0

    def similarity_search_with_filter(
        self,
        embedding: Embeddings,
        filters: dict[str, Any],
        top_k: int = 5,
    ) -> list[SimilaritySearchResult]:
        """Perform similarity search with metadata filtering.

        Note: This performs similarity search first, then filters results.
        The top_k parameter applies BEFORE filtering, so fewer than top_k
        results may be returned if filters are restrictive.

        Args:
            embedding: Query embedding vector
            filters: Dictionary of metadata key-value pairs to match
            top_k: Number of candidates to retrieve before filtering

        Returns:
            List of (rowid, text, distance) tuples matching filters

        Raises:
            ValidationError: If parameters are invalid
            TableNotFoundError: If table doesn't exist
        """
        validate_top_k(top_k)
        validate_metadata_filters(filters)
        logger.debug(f"Similarity search with filters: {filters}, top_k={top_k}")

        where_clause, params = build_metadata_where_clause(filters)
        try:
            cursor = self.connection.cursor()
            # Use subquery to get similarity results first, then filter
            cursor.execute(
                f"""
                SELECT
                    sim.rowid,
                    sim.text,
                    sim.distance
                FROM (
                    SELECT
                        e.rowid AS rowid,
                        e.text AS text,
                        e.metadata AS metadata,
                        v.distance AS distance
                    FROM {self.table} AS e
                    INNER JOIN {self.table}_vec AS v on v.rowid = e.rowid
                    WHERE v.text_embedding MATCH ? AND k = ?
                    ORDER BY v.distance
                ) AS sim
                WHERE {where_clause}
                """,
                [serialize_f32(embedding), top_k] + params,
            )
            results = cursor.fetchall()
            logger.debug(f"Filtered similarity search returned {len(results)} results")
            return [(row["rowid"], row["text"], row["distance"]) for row in results]
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                logger.error(f"Table '{self.table}' not found during similarity search")
                raise TableNotFoundError(
                    f"Table '{self.table}' or '{self.table}_vec' does not exist. "
                    "Call create_table() first."
                ) from e
            raise

    def export_to_json(
        self,
        filepath: str,
        include_embeddings: bool = True,
        filters: dict[str, Any] | None = None,
        batch_size: int = 1000,
    ) -> int:
        """Export records to JSON Lines format.

        Args:
            filepath: Path to output file
            include_embeddings: Whether to include embeddings in export
            filters: Optional metadata filters to apply
            batch_size: Number of records to process at once

        Returns:
            Number of records exported
        """
        return io_module.export_to_json(
            self, filepath, include_embeddings, filters, batch_size
        )

    def import_from_json(
        self, filepath: str, skip_duplicates: bool = False, batch_size: int = 1000
    ) -> int:
        """Import records from JSON Lines format.

        Args:
            filepath: Path to input file
            skip_duplicates: Whether to skip records with existing rowids
            batch_size: Number of records to import at once

        Returns:
            Number of records imported
        """
        return io_module.import_from_json(self, filepath, skip_duplicates, batch_size)

    def export_to_csv(
        self,
        filepath: str,
        include_embeddings: bool = False,
        filters: dict[str, Any] | None = None,
        batch_size: int = 1000,
    ) -> int:
        """Export records to CSV format.

        Args:
            filepath: Path to output file
            include_embeddings: Whether to include embeddings (as JSON string)
            filters: Optional metadata filters to apply
            batch_size: Number of records to process at once

        Returns:
            Number of records exported
        """
        return io_module.export_to_csv(
            self, filepath, include_embeddings, filters, batch_size
        )

    def import_from_csv(
        self, filepath: str, skip_duplicates: bool = False, batch_size: int = 1000
    ) -> int:
        """Import records from CSV format.

        Args:
            filepath: Path to input file
            skip_duplicates: Whether to skip records with existing rowids
            batch_size: Number of records to import at once

        Returns:
            Number of records imported
        """
        return io_module.import_from_csv(self, filepath, skip_duplicates, batch_size)

    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """Context manager for atomic transactions.

        Example:
            with client.transaction():
                client.add([...], [...])
                client.update_many([...])
        """
        logger.debug("Starting transaction")
        self._in_transaction = True
        try:
            yield
            self.connection.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
        finally:
            self._in_transaction = False

    def close(self) -> None:
        """Close or return the connection to pool, suppressing close errors."""
        try:
            logger.debug(f"Closing connection for table '{self.table}'")
            if self._pool:
                self._pool.return_connection(self.connection)
                logger.info(f"Connection returned to pool for table '{self.table}'")
            else:
                self.connection.close()
                logger.info(f"Connection closed for table '{self.table}'")
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
