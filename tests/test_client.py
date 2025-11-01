"""Integration tests for SQLiteVecClient."""

import pytest

from sqlite_vec_client import (
    DimensionMismatchError,
    SQLiteVecClient,
    TableNameError,
    TableNotFoundError,
    ValidationError,
)


@pytest.mark.integration
class TestClientInitialization:
    """Tests for client initialization."""

    def test_init_with_table_name(self, temp_db):
        """Test initialization with table name."""
        client = SQLiteVecClient(table="valid_table", db_path=temp_db)
        assert client.table == "valid_table"
        client.close()


@pytest.mark.integration
class TestCreateTable:
    """Tests for create_table method."""

    def test_create_table_basic(self, client):
        """Test basic table creation."""
        client.create_table(dim=3)
        assert client.count() == 0

    def test_create_table_with_distance_metrics(self, client):
        """Test table creation with different distance metrics."""
        for distance in ["L1", "L2", "cosine"]:
            client.create_table(dim=3, distance=distance)

    def test_create_table_invalid_dimension(self, client):
        """Test that invalid dimension raises error."""
        with pytest.raises(ValidationError):
            client.create_table(dim=0)

    def test_create_table_validates_table_name(self, temp_db):
        """Test that create_table validates table name."""
        client = SQLiteVecClient(table="invalid-table", db_path=temp_db)
        with pytest.raises(TableNameError):
            client.create_table(dim=3)
        client.close()


@pytest.mark.integration
class TestAddRecords:
    """Tests for add method."""

    def test_add_single_record(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test adding a single record."""
        rowids = client_with_table.add(
            texts=[sample_texts[0]], embeddings=[sample_embeddings[0]]
        )
        assert len(rowids) == 1
        assert client_with_table.count() == 1

    def test_add_multiple_records(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test adding multiple records."""
        rowids = client_with_table.add(texts=sample_texts, embeddings=sample_embeddings)
        assert len(rowids) == 3
        assert client_with_table.count() == 3

    def test_add_with_metadata(
        self, client_with_table, sample_texts, sample_embeddings, sample_metadata
    ):
        """Test adding records with metadata."""
        rowids = client_with_table.add(
            texts=sample_texts, embeddings=sample_embeddings, metadata=sample_metadata
        )
        assert len(rowids) == 3

    def test_add_mismatched_lengths(self, client_with_table):
        """Test that mismatched lengths raise error."""
        with pytest.raises(ValidationError):
            client_with_table.add(texts=["a", "b"], embeddings=[[1.0, 2.0, 3.0]])

    def test_add_invalid_embedding_dimension(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test that embeddings with wrong dimension raise error."""
        invalid_embeddings = [[0.1, 0.2]] * len(sample_texts)
        with pytest.raises(DimensionMismatchError):
            client_with_table.add(texts=sample_texts, embeddings=invalid_embeddings)


@pytest.mark.integration
class TestSimilaritySearch:
    """Tests for similarity_search method."""

    def test_similarity_search_basic(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test basic similarity search."""
        client_with_table.add(texts=sample_texts, embeddings=sample_embeddings)
        results = client_with_table.similarity_search(
            embedding=[0.1, 0.2, 0.3], top_k=2
        )
        assert len(results) == 2
        assert all(len(r) == 3 for r in results)  # (rowid, text, distance)

    def test_similarity_search_without_table(self, client):
        """Test search without table raises error."""
        with pytest.raises(TableNotFoundError):
            client.similarity_search(embedding=[0.1, 0.2, 0.3])

    def test_similarity_search_invalid_top_k(self, client_with_table):
        """Test that invalid top_k raises error."""
        with pytest.raises(ValidationError):
            client_with_table.similarity_search(embedding=[0.1, 0.2, 0.3], top_k=0)

    def test_similarity_search_invalid_dimension(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test that query embedding with wrong dimension raises error."""
        client_with_table.add(texts=sample_texts, embeddings=sample_embeddings)
        with pytest.raises(DimensionMismatchError):
            client_with_table.similarity_search(embedding=[0.1, 0.2], top_k=1)


@pytest.mark.integration
class TestGetRecords:
    """Tests for get methods."""

    def test_get_existing(self, client_with_table, sample_texts, sample_embeddings):
        """Test getting existing record by ID."""
        rowids = client_with_table.add(texts=sample_texts, embeddings=sample_embeddings)
        result = client_with_table.get(rowids[0])
        assert result is not None
        assert result[0] == rowids[0]
        assert result[1] == sample_texts[0]

    def test_get_nonexistent(self, client_with_table):
        """Test getting nonexistent record returns None."""
        result = client_with_table.get(999)
        assert result is None

    def test_get_many(self, client_with_table, sample_texts, sample_embeddings):
        """Test getting multiple records."""
        rowids = client_with_table.add(texts=sample_texts, embeddings=sample_embeddings)
        results = client_with_table.get_many(rowids[:2])
        assert len(results) == 2

    def test_get_many_empty(self, client_with_table):
        """Test getting empty list returns empty list."""
        results = client_with_table.get_many([])
        assert results == []


@pytest.mark.integration
class TestUpdateRecords:
    """Tests for update method."""

    def test_update_text(self, client_with_table, sample_texts, sample_embeddings):
        """Test updating text field."""
        rowids = client_with_table.add(
            texts=[sample_texts[0]], embeddings=[sample_embeddings[0]]
        )
        updated = client_with_table.update(rowids[0], text="updated text")
        assert updated is True
        result = client_with_table.get(rowids[0])
        assert result[1] == "updated text"

    def test_update_metadata(self, client_with_table, sample_texts, sample_embeddings):
        """Test updating metadata field."""
        rowids = client_with_table.add(
            texts=[sample_texts[0]], embeddings=[sample_embeddings[0]]
        )
        new_metadata = {"key": "value"}
        updated = client_with_table.update(rowids[0], metadata=new_metadata)
        assert updated is True
        result = client_with_table.get(rowids[0])
        assert result[2] == new_metadata

    def test_update_nonexistent(self, client_with_table):
        """Test updating nonexistent record returns False."""
        updated = client_with_table.update(999, text="test")
        assert updated is False


@pytest.mark.integration
class TestDeleteRecords:
    """Tests for delete methods."""

    def test_delete(self, client_with_table, sample_texts, sample_embeddings):
        """Test deleting record by ID."""
        rowids = client_with_table.add(
            texts=[sample_texts[0]], embeddings=[sample_embeddings[0]]
        )
        deleted = client_with_table.delete(rowids[0])
        assert deleted is True
        assert client_with_table.count() == 0

    def test_delete_nonexistent(self, client_with_table):
        """Test deleting nonexistent record returns False."""
        deleted = client_with_table.delete(999)
        assert deleted is False

    def test_delete_many(self, client_with_table, sample_texts, sample_embeddings):
        """Test deleting multiple records."""
        rowids = client_with_table.add(texts=sample_texts, embeddings=sample_embeddings)
        deleted_count = client_with_table.delete_many(rowids[:2])
        assert deleted_count == 2
        assert client_with_table.count() == 1


@pytest.mark.integration
class TestCountRecords:
    """Tests for count method."""

    def test_count_empty_table(self, client_with_table):
        """Test counting records in empty table."""
        assert client_with_table.count() == 0

    def test_count_with_records(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test counting records after adding."""
        client_with_table.add(texts=sample_texts, embeddings=sample_embeddings)
        assert client_with_table.count() == 3


@pytest.mark.integration
class TestContextManager:
    """Tests for context manager protocol."""

    def test_context_manager(self, temp_db):
        """Test using client as context manager."""
        with SQLiteVecClient(table="test", db_path=temp_db) as client:
            client.create_table(dim=3)
            assert client.count() == 0


@pytest.mark.integration
class TestBulkOperations:
    """Tests for bulk operations."""

    def test_update_many(self, client_with_table, sample_texts, sample_embeddings):
        """Test updating multiple records."""
        rowids = client_with_table.add(texts=sample_texts, embeddings=sample_embeddings)
        updates = [
            (rowids[0], "updated 1", None, None),
            (rowids[1], "updated 2", {"key": "val"}, None),
        ]
        count = client_with_table.update_many(updates)
        assert count == 2
        result = client_with_table.get(rowids[0])
        assert result[1] == "updated 1"

    def test_update_many_empty(self, client_with_table):
        """Test update_many with empty list."""
        count = client_with_table.update_many([])
        assert count == 0

    def test_get_all_generator(self, client_with_table):
        """Test get_all generator."""
        texts = [f"text {i}" for i in range(10)]
        embeddings = [[float(i)] * 3 for i in range(10)]
        client_with_table.add(texts=texts, embeddings=embeddings)
        results = list(client_with_table.get_all(batch_size=3))
        assert len(results) == 10

    def test_get_all_empty_table(self, client_with_table):
        """Test get_all on empty table."""
        results = list(client_with_table.get_all())
        assert len(results) == 0

    def test_transaction_commit(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test transaction commits on success."""
        with client_with_table.transaction():
            client_with_table.add(texts=sample_texts, embeddings=sample_embeddings)
        assert client_with_table.count() == 3

    def test_transaction_rollback(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test transaction rolls back on error."""
        try:
            with client_with_table.transaction():
                client_with_table.add(texts=sample_texts, embeddings=sample_embeddings)
                raise ValueError("Test error")
        except ValueError:
            pass
        assert client_with_table.count() == 0


@pytest.mark.integration
class TestMetadataFiltering:
    """Tests for metadata filtering methods."""

    def test_filter_by_metadata_single_field(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test filtering by single metadata field."""
        metadata = [
            {"category": "python"},
            {"category": "java"},
            {"category": "python"},
        ]
        client_with_table.add(
            texts=sample_texts, embeddings=sample_embeddings, metadata=metadata
        )
        results = client_with_table.filter_by_metadata({"category": "python"})
        assert len(results) == 2
        assert all(r[2]["category"] == "python" for r in results)

    def test_filter_by_metadata_multiple_fields(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test filtering by multiple metadata fields."""
        metadata = [
            {"category": "python", "year": 2024},
            {"category": "python", "year": 2023},
            {"category": "java", "year": 2024},
        ]
        client_with_table.add(
            texts=sample_texts, embeddings=sample_embeddings, metadata=metadata
        )
        results = client_with_table.filter_by_metadata(
            {"category": "python", "year": 2024}
        )
        assert len(results) == 1
        assert results[0][2]["category"] == "python"
        assert results[0][2]["year"] == 2024

    def test_filter_by_metadata_no_matches(self, client_with_table):
        """Test filtering with no matches returns empty list."""
        results = client_with_table.filter_by_metadata({"category": "nonexistent"})
        assert results == []

    def test_filter_by_metadata_with_pagination(
        self, client_with_table, sample_embeddings
    ):
        """Test filtering with pagination."""
        texts = [f"text {i}" for i in range(10)]
        embeddings = [sample_embeddings[0]] * 10
        metadata = [{"category": "test"} for _ in range(10)]
        client_with_table.add(texts=texts, embeddings=embeddings, metadata=metadata)
        results = client_with_table.filter_by_metadata(
            {"category": "test"}, limit=5, offset=0
        )
        assert len(results) == 5
        results_page2 = client_with_table.filter_by_metadata(
            {"category": "test"}, limit=5, offset=5
        )
        assert len(results_page2) == 5

    def test_count_by_metadata(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test counting records by metadata."""
        metadata = [
            {"category": "python"},
            {"category": "java"},
            {"category": "python"},
        ]
        client_with_table.add(
            texts=sample_texts, embeddings=sample_embeddings, metadata=metadata
        )
        count = client_with_table.count_by_metadata({"category": "python"})
        assert count == 2

    def test_similarity_search_with_filter(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test similarity search with metadata filtering."""
        metadata = [
            {"category": "python"},
            {"category": "java"},
            {"category": "python"},
        ]
        client_with_table.add(
            texts=sample_texts, embeddings=sample_embeddings, metadata=metadata
        )
        results = client_with_table.similarity_search_with_filter(
            embedding=[0.1, 0.2, 0.3], filters={"category": "python"}, top_k=5
        )
        assert len(results) <= 2
        for rowid, _, _ in results:
            record = client_with_table.get(rowid)
            assert record[2]["category"] == "python"

    def test_similarity_search_with_filter_no_matches(
        self, client_with_table, sample_texts, sample_embeddings
    ):
        """Test similarity search with filter that matches nothing."""
        metadata = [{"category": "python"}] * 3
        client_with_table.add(
            texts=sample_texts, embeddings=sample_embeddings, metadata=metadata
        )
        results = client_with_table.similarity_search_with_filter(
            embedding=[0.1, 0.2, 0.3], filters={"category": "java"}, top_k=5
        )
        assert results == []
