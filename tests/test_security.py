"""Security tests for sqlite-vec-client."""

import pytest

from sqlite_vec_client import (
    SQLiteVecClient,
    TableNameError,
    TableNotFoundError,
    ValidationError,
)


@pytest.mark.unit
class TestSQLInjectionPrevention:
    """Tests for SQL injection prevention."""

    def test_table_name_with_sql_injection(self, temp_db):
        """Test that SQL injection attempts in table names are blocked."""
        malicious_names = [
            "table; DROP TABLE users;",
            "table' OR '1'='1",
            "table--",
            "table/*comment*/",
            "table;DELETE FROM data",
        ]
        for name in malicious_names:
            client = SQLiteVecClient(table=name, db_path=temp_db)
            with pytest.raises(TableNameError):
                client.create_table(dim=3)
            client.close()

    def test_table_name_with_special_chars(self, temp_db):
        """Test that special characters in table names are rejected."""
        invalid_names = ["table-name", "table.name", "table name", "table@name"]
        for name in invalid_names:
            client = SQLiteVecClient(table=name, db_path=temp_db)
            with pytest.raises(TableNameError):
                client.create_table(dim=3)
            client.close()

    def test_table_name_starting_with_number(self, temp_db):
        """Test that table names starting with numbers are rejected."""
        client = SQLiteVecClient(table="123table", db_path=temp_db)
        with pytest.raises(TableNameError):
            client.create_table(dim=3)
        client.close()


@pytest.mark.unit
class TestInputValidationSecurity:
    """Tests for input validation security."""

    def test_negative_dimension(self, client):
        """Test that negative dimensions are rejected."""
        with pytest.raises(ValidationError, match="positive integer"):
            client.create_table(dim=-1)

    def test_zero_dimension(self, client):
        """Test that zero dimension is rejected."""
        with pytest.raises(ValidationError, match="positive integer"):
            client.create_table(dim=0)

    def test_negative_top_k(self, client_with_table):
        """Test that negative top_k is rejected."""
        with pytest.raises(ValidationError, match="positive integer"):
            client_with_table.similarity_search(embedding=[0.1, 0.2, 0.3], top_k=-1)

    def test_zero_top_k(self, client_with_table):
        """Test that zero top_k is rejected."""
        with pytest.raises(ValidationError, match="positive integer"):
            client_with_table.similarity_search(embedding=[0.1, 0.2, 0.3], top_k=0)

    def test_negative_batch_size(self, client_with_table):
        """Test that negative batch_size is rejected."""
        with pytest.raises(ValidationError, match="positive integer"):
            list(client_with_table.get_all(batch_size=-1))


@pytest.mark.integration
class TestErrorHandling:
    """Tests for proper error handling."""

    def test_operation_without_table(self, client):
        """Test that operations without table raise proper errors."""
        with pytest.raises(TableNotFoundError, match="does not exist"):
            client.similarity_search(embedding=[0.1, 0.2, 0.3])

    def test_add_without_table(self, client):
        """Test that adding records without table raises error."""
        with pytest.raises(TableNotFoundError, match="does not exist"):
            client.add(texts=["test"], embeddings=[[0.1, 0.2, 0.3]])

    def test_mismatched_texts_embeddings(self, client_with_table):
        """Test that mismatched list lengths are caught."""
        with pytest.raises(ValidationError, match="must match"):
            client_with_table.add(texts=["a", "b"], embeddings=[[0.1, 0.2, 0.3]])

    def test_mismatched_texts_metadata(self, client_with_table):
        """Test that mismatched texts and metadata are caught."""
        with pytest.raises(ValidationError, match="must match"):
            client_with_table.add(
                texts=["a", "b"],
                embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
                metadata=[{"x": 1}],
            )


@pytest.mark.unit
class TestTableNameValidation:
    """Tests for table name validation edge cases."""

    def test_empty_table_name(self, temp_db):
        """Test that empty table name is rejected."""
        client = SQLiteVecClient(table="", db_path=temp_db)
        with pytest.raises(TableNameError, match="cannot be empty"):
            client.create_table(dim=3)
        client.close()

    def test_valid_table_names(self, temp_db):
        """Test that valid table names are accepted."""
        valid_names = ["table", "my_table", "_private", "Table123", "t"]
        for name in valid_names:
            client = SQLiteVecClient(table=name, db_path=temp_db)
            assert client.table == name
            client.close()

    def test_table_name_with_underscore_prefix(self, temp_db):
        """Test that table names starting with underscore are valid."""
        client = SQLiteVecClient(table="_private_table", db_path=temp_db)
        assert client.table == "_private_table"
        client.close()


@pytest.mark.integration
class TestConnectionSecurity:
    """Tests for connection security."""

    def test_connection_closes_properly(self, temp_db):
        """Test that connections close without errors."""
        client = SQLiteVecClient(table="test", db_path=temp_db)
        client.create_table(dim=3)
        client.close()
        # Multiple closes should not raise
        client.close()

    def test_context_manager_closes_connection(self, temp_db):
        """Test that context manager properly closes connection."""
        with SQLiteVecClient(table="test", db_path=temp_db) as client:
            client.create_table(dim=3)
            assert client.connection is not None
        # Connection should be closed after context
