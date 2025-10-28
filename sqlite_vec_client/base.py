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

from .types import Embeddings, Metadata, Result, Rowids, SimilaritySearchResult, Text
from .utils import deserialize_f32, serialize_f32


class SQLiteVecClient:
    """Manage a text+embedding table and its sqlite-vec index.

    The client maintains two tables:
    - `{table}`: base table with columns `text`, `metadata`, `text_embedding`.
    - `{table}_vec`: `vec0` virtual table mirroring embeddings for ANN search.

    It exposes CRUD helpers and `similarity_search` over embeddings.
    """

    @staticmethod
    def create_connection(db_path: str) -> sqlite3.Connection:
        """Create a SQLite connection with sqlite-vec extension loaded."""
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
        connection.enable_load_extension(False)
        return connection

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
        """Initialize the client for a given base table and database file."""
        self.table = table
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
        """Create base table, vector table, and triggers to keep them in sync."""
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

    def similarity_search(
        self,
        embedding: Embeddings,
        top_k: int = 5,
    ) -> list[SimilaritySearchResult]:
        """Return top-k nearest neighbors for the given embedding."""
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
        return [(row["rowid"], row["text"], row["distance"]) for row in results]

    def add(
        self,
        texts: list[Text],
        embeddings: list[Embeddings],
        metadata: list[Metadata] | None = None,
    ) -> Rowids:
        """Insert texts with embeddings (and optional metadata) and return rowids."""
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
        return [row["rowid"] for row in results]

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
        """List records with pagination and order by rowid."""
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
        return cur.rowcount > 0

    def delete_by_id(self, rowid: int) -> bool:
        """Delete a single record by rowid; return True if a row was removed."""
        cur = self.connection.cursor()
        cur.execute(f"DELETE FROM {self.table} WHERE rowid = ?", [rowid])
        self.connection.commit()
        return cur.rowcount > 0

    def delete_many(self, rowids: list[int]) -> int:
        """Delete multiple records by rowids; return number of rows removed."""
        if not rowids:
            return 0
        placeholders = ",".join(["?"] * len(rowids))
        cur = self.connection.cursor()
        cur.execute(
            f"DELETE FROM {self.table} WHERE rowid IN ({placeholders})",
            rowids,
        )
        self.connection.commit()
        return cur.rowcount

    def close(self) -> None:
        """Close the underlying SQLite connection, suppressing close errors."""
        try:
            self.connection.close()
        except Exception:
            pass
