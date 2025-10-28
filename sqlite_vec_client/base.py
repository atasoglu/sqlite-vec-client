"""High-level client for vector search on SQLite using the sqlite-vec extension.

This module provides `SQLiteVecClient`, a thin wrapper around `sqlite3` and
`sqlite-vec` to store texts, JSON metadata, and float32 embeddings, and to run
similarity search through a virtual vector table.
"""

from __future__ import annotations

import json
import sqlite3
from types import TracebackType
from typing import Any, Literal

import sqlite_vec

from .exceptions import ConnectionError as VecConnectionError
from .exceptions import TableNotFoundError
from .logger import get_logger
from .types import Embeddings, Metadata, Result, Rowids, SimilaritySearchResult, Text
from .utils import deserialize_f32, serialize_f32
from .validation import (
    validate_dimension,
    validate_embeddings_match,
    validate_limit,
    validate_offset,
    validate_table_name,
    validate_top_k,
)

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

    def __init__(self, table: str, db_path: str) -> None:
        """Initialize the client for a given base table and database file.

        Args:
            table: Name of the base table
            db_path: Path to SQLite database file

        Raises:
            TableNameError: If table name is invalid
            VecConnectionError: If connection fails
        """
        validate_table_name(table)
        self.table = table
        logger.debug(f"Initializing SQLiteVecClient for table: {table}")
        self.connection = self.create_connection(db_path)

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
            ValidationError: If dimension is invalid
        """
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
            max_id = self.connection.execute(
                f"SELECT max(rowid) as rowid FROM {self.table}"
            ).fetchone()["rowid"]

            if max_id is None:
                max_id = 0

            if metadata is None:
                metadata = [dict() for _ in texts]

            data_input = [
                (text, json.dumps(md), serialize_f32(embedding))
                for text, md, embedding in zip(texts, metadata, embeddings)
            ]
            self.connection.executemany(
                f"""INSERT INTO {self.table}(text, metadata, text_embedding)
                VALUES (?,?,?)""",
                data_input,
            )
            self.connection.commit()
            results = self.connection.execute(
                f"SELECT rowid FROM {self.table} WHERE rowid > {max_id}"
            )
            rowids = [row["rowid"] for row in results]
            logger.info(f"Added {len(rowids)} records to table '{self.table}'")
            return rowids
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                logger.error(f"Table '{self.table}' not found during add operation")
                raise TableNotFoundError(
                    f"Table '{self.table}' does not exist. Call create_table() first."
                ) from e
            raise

    def get_by_id(self, rowid: int) -> Result | None:
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

    def get_by_text(self, text: str) -> list[Result]:
        """Get all records with exact `text`, ordered by rowid ascending."""
        cursor = self.connection.cursor()
        cursor.execute(
            f"""
            SELECT rowid, text, metadata, text_embedding FROM {self.table}
            WHERE text = ?
            ORDER BY rowid ASC
            """,
            [text],
        )
        rows = cursor.fetchall()
        return self.rows_to_results(rows)

    def get_by_metadata(self, metadata: dict[str, Any]) -> list[Result]:
        """Get all records whose metadata exactly equals the given dict."""
        cursor = self.connection.cursor()
        cursor.execute(
            f"""
            SELECT rowid, text, metadata, text_embedding FROM {self.table}
            WHERE metadata = ?
            ORDER BY rowid ASC
            """,
            [json.dumps(metadata)],
        )
        rows = cursor.fetchall()
        return self.rows_to_results(rows)

    def list_results(
        self,
        limit: int = 50,
        offset: int = 0,
        order: Literal["asc", "desc"] = "asc",
    ) -> list[Result]:
        """List records with pagination and order by rowid.

        Args:
            limit: Maximum number of results (must be positive)
            offset: Number of results to skip (must be non-negative)
            order: Sort order ('asc' or 'desc')

        Returns:
            List of (rowid, text, metadata, embedding) tuples

        Raises:
            ValidationError: If limit or offset is invalid
        """
        validate_limit(limit)
        validate_offset(offset)
        cursor = self.connection.cursor()
        cursor.execute(
            f"""
            SELECT rowid, text, metadata, text_embedding FROM {self.table}
            ORDER BY rowid {order.upper()}
            LIMIT ? OFFSET ?
            """,
            [limit, offset],
        )
        rows = cursor.fetchall()
        return self.rows_to_results(rows)

    def count(self) -> int:
        """Return the total number of rows in the base table."""
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT COUNT(1) as c FROM {self.table}")
        row = cursor.fetchone()
        return int(row["c"]) if row is not None else 0

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
        self.connection.commit()
        updated = cur.rowcount > 0
        if updated:
            logger.debug(f"Successfully updated record with rowid={rowid}")
        return updated

    def delete_by_id(self, rowid: int) -> bool:
        """Delete a single record by rowid; return True if a row was removed."""
        logger.debug(f"Deleting record with rowid={rowid}")
        cur = self.connection.cursor()
        cur.execute(f"DELETE FROM {self.table} WHERE rowid = ?", [rowid])
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
        placeholders = ",".join(["?"] * len(rowids))
        cur = self.connection.cursor()
        cur.execute(
            f"DELETE FROM {self.table} WHERE rowid IN ({placeholders})",
            rowids,
        )
        self.connection.commit()
        deleted_count = cur.rowcount
        logger.info(f"Deleted {deleted_count} records from table '{self.table}'")
        return deleted_count

    def close(self) -> None:
        """Close the underlying SQLite connection, suppressing close errors."""
        try:
            logger.debug(f"Closing connection for table '{self.table}'")
            self.connection.close()
            logger.info(f"Connection closed for table '{self.table}'")
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
