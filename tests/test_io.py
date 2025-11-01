"""Tests for import/export functionality."""

import json

import pytest

from sqlite_vec_client import SQLiteVecClient


@pytest.mark.integration
class TestJSONExportImport:
    """Tests for JSON export/import."""

    def test_export_import_roundtrip(self, tmp_path, sample_texts, sample_embeddings):
        """Test export and import maintains data integrity."""
        # Setup
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)

        metadata = [{"id": i} for i in range(len(sample_texts))]
        client.add(texts=sample_texts, embeddings=sample_embeddings, metadata=metadata)

        # Export
        export_path = str(tmp_path / "export.jsonl")
        count = client.export_to_json(export_path)
        assert count == 3

        # Clear table
        for rowid in range(1, 4):
            client.delete(rowid)
        assert client.count() == 0

        # Import
        count = client.import_from_json(export_path)
        assert count == 3
        assert client.count() == 3

        # Verify data
        results = list(client.get_all())
        assert len(results) == 3
        for i, (rowid, text, meta, emb) in enumerate(results):
            assert text == sample_texts[i]
            assert meta == metadata[i]
            assert emb == pytest.approx(sample_embeddings[i])

        client.close()

    def test_export_without_embeddings(self, tmp_path, sample_texts, sample_embeddings):
        """Test export without embeddings."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)
        client.add(texts=sample_texts, embeddings=sample_embeddings)

        export_path = str(tmp_path / "export.jsonl")
        count = client.export_to_json(export_path, include_embeddings=False)
        assert count == 3

        # Verify embeddings not in file
        with open(export_path) as f:
            for line in f:
                record = json.loads(line)
                assert "embedding" not in record
                assert "text" in record
                assert "metadata" in record

        client.close()

    def test_import_skip_duplicates(self, tmp_path, sample_texts, sample_embeddings):
        """Test that duplicate records are skipped when requested."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)
        client.add(texts=sample_texts, embeddings=sample_embeddings)

        export_path = str(tmp_path / "export.jsonl")
        client.export_to_json(export_path)

        imported = client.import_from_json(export_path, skip_duplicates=True)
        assert imported == 0
        assert client.count() == 3

        client.close()

    def test_import_missing_embedding_raises(
        self, tmp_path, sample_texts, sample_embeddings
    ):
        """Test that importing without embedding data raises error."""
        export_path = tmp_path / "invalid.jsonl"
        with export_path.open("w", encoding="utf-8") as f:
            json.dump({"rowid": 1, "text": "hello", "metadata": {"a": 1}}, f)
            f.write("\n")

        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)

        with pytest.raises(ValueError, match="missing 'embedding'"):
            client.import_from_json(str(export_path))

        client.close()

    def test_backup_and_restore_helpers(
        self, tmp_path, sample_texts, sample_embeddings
    ):
        """Test high-level backup and restore helpers."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)
        client.add(texts=sample_texts, embeddings=sample_embeddings)

        backup_path = str(tmp_path / "backup.jsonl")
        count = client.backup(backup_path)
        assert count == 3

        for rowid in range(1, 4):
            client.delete(rowid)
        assert client.count() == 0

        restored = client.restore(backup_path)
        assert restored == 3
        assert client.count() == 3

        client.close()

    def test_export_with_filters(self, tmp_path, sample_texts, sample_embeddings):
        """Test export with metadata filters."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)

        metadata = [{"category": "A"}, {"category": "B"}, {"category": "A"}]
        client.add(texts=sample_texts, embeddings=sample_embeddings, metadata=metadata)

        export_path = str(tmp_path / "export.jsonl")
        count = client.export_to_json(export_path, filters={"category": "A"})
        assert count == 2

        # Verify only filtered records exported
        with open(export_path) as f:
            lines = f.readlines()
            assert len(lines) == 2
            for line in lines:
                record = json.loads(line)
                assert record["metadata"]["category"] == "A"

        client.close()

    def test_import_nonexistent_file(self, tmp_path):
        """Test import from nonexistent file raises error."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)

        with pytest.raises(FileNotFoundError):
            client.import_from_json("nonexistent.jsonl")

        client.close()


@pytest.mark.integration
class TestCSVExportImport:
    """Tests for CSV export/import."""

    def test_export_import_roundtrip(self, tmp_path, sample_texts, sample_embeddings):
        """Test CSV export and import maintains data integrity."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)

        metadata = [{"id": i} for i in range(len(sample_texts))]
        client.add(texts=sample_texts, embeddings=sample_embeddings, metadata=metadata)

        # Export
        export_path = str(tmp_path / "export.csv")
        count = client.export_to_csv(export_path, include_embeddings=True)
        assert count == 3

        # Clear table
        for rowid in range(1, 4):
            client.delete(rowid)
        assert client.count() == 0

        # Import
        count = client.import_from_csv(export_path)
        assert count == 3
        assert client.count() == 3

        # Verify data
        results = list(client.get_all())
        assert len(results) == 3

        client.close()

    def test_export_without_embeddings(self, tmp_path, sample_texts, sample_embeddings):
        """Test CSV export without embeddings."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)
        client.add(texts=sample_texts, embeddings=sample_embeddings)

        export_path = str(tmp_path / "export.csv")
        count = client.export_to_csv(export_path, include_embeddings=False)
        assert count == 3

        # Verify file structure
        with open(export_path) as f:
            header = f.readline().strip()
            assert "embedding" not in header
            assert "text" in header
            assert "metadata" in header

        client.close()

    def test_import_without_embedding_column_raises(
        self, tmp_path, sample_texts, sample_embeddings
    ):
        """Test importing CSV without embeddings raises error."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)
        client.add(texts=sample_texts, embeddings=sample_embeddings)

        export_path = str(tmp_path / "export.csv")
        client.export_to_csv(export_path, include_embeddings=False)

        with pytest.raises(ValueError, match="missing 'embedding'"):
            client.import_from_csv(export_path)

        client.close()

    def test_backup_and_restore_csv(self, tmp_path, sample_texts, sample_embeddings):
        """Test backup and restore helpers with CSV format."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)
        client.add(texts=sample_texts, embeddings=sample_embeddings)

        backup_path = str(tmp_path / "backup.csv")
        count = client.backup(backup_path, format="csv", include_embeddings=True)
        assert count == 3

        for rowid in range(1, 4):
            client.delete(rowid)

        restored = client.restore(backup_path, format="csv")
        assert restored == 3
        assert client.count() == 3

        client.close()

    def test_export_with_filters(self, tmp_path, sample_texts, sample_embeddings):
        """Test CSV export with metadata filters."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)

        metadata = [{"category": "A"}, {"category": "B"}, {"category": "A"}]
        client.add(texts=sample_texts, embeddings=sample_embeddings, metadata=metadata)

        export_path = str(tmp_path / "export.csv")
        count = client.export_to_csv(export_path, filters={"category": "A"})
        assert count == 2

        client.close()

    def test_import_nonexistent_file(self, tmp_path):
        """Test import from nonexistent file raises error."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)

        with pytest.raises(FileNotFoundError):
            client.import_from_csv("nonexistent.csv")

        client.close()


@pytest.mark.integration
class TestBatchProcessing:
    """Tests for batch processing during import/export."""

    def test_large_export_json(self, tmp_path):
        """Test exporting large dataset in batches."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)

        # Add 100 records
        texts = [f"text {i}" for i in range(100)]
        embeddings = [[float(i), float(i + 1), float(i + 2)] for i in range(100)]
        client.add(texts=texts, embeddings=embeddings)

        # Export with small batch size
        export_path = str(tmp_path / "export.jsonl")
        count = client.export_to_json(export_path, batch_size=10)
        assert count == 100

        # Verify all records exported
        with open(export_path) as f:
            lines = f.readlines()
            assert len(lines) == 100

        client.close()

    def test_large_import_json(self, tmp_path):
        """Test importing large dataset in batches."""
        db_path = str(tmp_path / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)
        client.create_table(dim=3)

        # Create large JSON file
        export_path = tmp_path / "export.jsonl"
        with open(export_path, "w") as f:
            for i in range(100):
                record = {
                    "rowid": i + 1,
                    "text": f"text {i}",
                    "metadata": {"id": i},
                    "embedding": [float(i), float(i + 1), float(i + 2)],
                }
                f.write(json.dumps(record) + "\n")

        # Import with small batch size
        count = client.import_from_json(str(export_path), batch_size=10)
        assert count == 100
        assert client.count() == 100

        client.close()
