"""Import/export utilities for SQLiteVecClient."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .logger import get_logger
from .types import Embeddings, Metadata

if TYPE_CHECKING:
    from .base import SQLiteVecClient

logger = get_logger()


def export_to_json(
    client: SQLiteVecClient,
    filepath: str,
    include_embeddings: bool = True,
    filters: dict[str, Any] | None = None,
    batch_size: int = 1000,
) -> int:
    """Export records to JSON Lines format.

    Args:
        client: SQLiteVecClient instance
        filepath: Path to output file
        include_embeddings: Whether to include embeddings in export
        filters: Optional metadata filters to apply
        batch_size: Number of records to process at once

    Returns:
        Number of records exported
    """
    logger.info(f"Exporting to JSON: {filepath}")
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with path.open("w", encoding="utf-8") as f:
        if filters:
            records = client.filter_by_metadata(filters, limit=batch_size, offset=0)
            offset = 0
            while records:
                for rowid, text, metadata, embedding in records:
                    record = {
                        "rowid": rowid,
                        "text": text,
                        "metadata": metadata,
                    }
                    if include_embeddings:
                        record["embedding"] = embedding
                    f.write(json.dumps(record) + "\n")
                    count += 1
                offset += batch_size
                records = client.filter_by_metadata(
                    filters, limit=batch_size, offset=offset
                )
        else:
            for rowid, text, metadata, embedding in client.get_all(
                batch_size=batch_size
            ):
                record = {
                    "rowid": rowid,
                    "text": text,
                    "metadata": metadata,
                }
                if include_embeddings:
                    record["embedding"] = embedding
                f.write(json.dumps(record) + "\n")
                count += 1

    logger.info(f"Exported {count} records to {filepath}")
    return count


def import_from_json(
    client: SQLiteVecClient,
    filepath: str,
    skip_duplicates: bool = False,
    batch_size: int = 1000,
) -> int:
    """Import records from JSON Lines format.

    Args:
        client: SQLiteVecClient instance
        filepath: Path to input file
        skip_duplicates: Whether to skip records with existing rowids
        batch_size: Number of records to import at once

    Returns:
        Number of records imported
    """
    logger.info(f"Importing from JSON: {filepath}")
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    count = 0
    texts: list[str] = []
    embeddings: list[Embeddings] = []
    metadata_list: list[Metadata] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            embedding = record.get("embedding")
            if embedding is None:
                raise ValueError(
                    "JSON record is missing 'embedding'. Export with "
                    "include_embeddings=True to support import."
                )

            record_rowid = record.get("rowid")
            if skip_duplicates and isinstance(record_rowid, int):
                if client.get(record_rowid) is not None:
                    continue

            texts.append(record["text"])
            metadata_list.append(record.get("metadata", {}))
            embeddings.append(embedding)

            if len(texts) >= batch_size:
                client.add(texts=texts, embeddings=embeddings, metadata=metadata_list)
                count += len(texts)
                texts, embeddings, metadata_list = [], [], []

        # Import remaining records
        if texts:
            client.add(texts=texts, embeddings=embeddings, metadata=metadata_list)
            count += len(texts)

    logger.info(f"Imported {count} records from {filepath}")
    return count


def export_to_csv(
    client: SQLiteVecClient,
    filepath: str,
    include_embeddings: bool = False,
    filters: dict[str, Any] | None = None,
    batch_size: int = 1000,
) -> int:
    """Export records to CSV format.

    Args:
        client: SQLiteVecClient instance
        filepath: Path to output file
        include_embeddings: Whether to include embeddings (as JSON string)
        filters: Optional metadata filters to apply
        batch_size: Number of records to process at once

    Returns:
        Number of records exported
    """
    logger.info(f"Exporting to CSV: {filepath}")
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    fieldnames = ["rowid", "text", "metadata"]
    if include_embeddings:
        fieldnames.append("embedding")

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        if filters:
            records = client.filter_by_metadata(filters, limit=batch_size, offset=0)
            offset = 0
            while records:
                for rowid, text, metadata, embedding in records:
                    row = {
                        "rowid": rowid,
                        "text": text,
                        "metadata": json.dumps(metadata),
                    }
                    if include_embeddings:
                        row["embedding"] = json.dumps(embedding)
                    writer.writerow(row)
                    count += 1
                offset += batch_size
                records = client.filter_by_metadata(
                    filters, limit=batch_size, offset=offset
                )
        else:
            for rowid, text, metadata, embedding in client.get_all(
                batch_size=batch_size
            ):
                row = {
                    "rowid": rowid,
                    "text": text,
                    "metadata": json.dumps(metadata),
                }
                if include_embeddings:
                    row["embedding"] = json.dumps(embedding)
                writer.writerow(row)
                count += 1

    logger.info(f"Exported {count} records to {filepath}")
    return count


def import_from_csv(
    client: SQLiteVecClient,
    filepath: str,
    skip_duplicates: bool = False,
    batch_size: int = 1000,
) -> int:
    """Import records from CSV format.

    Args:
        client: SQLiteVecClient instance
        filepath: Path to input file
        skip_duplicates: Whether to skip records with existing rowids
        batch_size: Number of records to import at once

    Returns:
        Number of records imported
    """
    logger.info(f"Importing from CSV: {filepath}")
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    count = 0
    texts: list[str] = []
    embeddings: list[Embeddings] = []
    metadata_list: list[Metadata] = []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV file must include headers")
        if "embedding" not in reader.fieldnames:
            raise ValueError(
                "CSV file is missing 'embedding' column. Export with "
                "include_embeddings=True to support import."
            )
        if "text" not in reader.fieldnames or "metadata" not in reader.fieldnames:
            raise ValueError("CSV file must include 'text' and 'metadata' columns")
        for row in reader:
            record_rowid = row.get("rowid")
            parsed_rowid = int(record_rowid) if record_rowid else None
            if skip_duplicates and parsed_rowid is not None:
                if client.get(parsed_rowid) is not None:
                    continue

            if row.get("embedding") is None or row["embedding"].strip() == "":
                raise ValueError(
                    "CSV record is missing embedding data. Export with "
                    "include_embeddings=True."
                )

            texts.append(row["text"])
            metadata_list.append(json.loads(row["metadata"]))
            embeddings.append(json.loads(row["embedding"]))

            if len(texts) >= batch_size:
                client.add(texts=texts, embeddings=embeddings, metadata=metadata_list)
                count += len(texts)
                texts, embeddings, metadata_list = [], [], []

        # Import remaining records
        if texts:
            client.add(texts=texts, embeddings=embeddings, metadata=metadata_list)
            count += len(texts)

    logger.info(f"Imported {count} records from {filepath}")
    return count
