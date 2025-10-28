"""Unit tests for validation functions."""

import pytest

from sqlite_vec_client.exceptions import (
    DimensionMismatchError,
    TableNameError,
    ValidationError,
)
from sqlite_vec_client.validation import (
    validate_dimension,
    validate_embedding_dimension,
    validate_embeddings_match,
    validate_limit,
    validate_offset,
    validate_table_name,
    validate_top_k,
)


@pytest.mark.unit
class TestValidateTableName:
    """Tests for validate_table_name function."""

    def test_valid_table_names(self):
        """Test that valid table names pass validation."""
        valid_names = ["table", "my_table", "_private", "Table123", "t"]
        for name in valid_names:
            validate_table_name(name)  # Should not raise

    def test_empty_table_name(self):
        """Test that empty table name raises error."""
        with pytest.raises(TableNameError, match="cannot be empty"):
            validate_table_name("")

    def test_invalid_characters(self):
        """Test that invalid characters raise error."""
        invalid_names = ["table-name", "table.name", "table name", "table;drop"]
        for name in invalid_names:
            with pytest.raises(TableNameError):
                validate_table_name(name)

    def test_starts_with_number(self):
        """Test that table name starting with number raises error."""
        with pytest.raises(TableNameError):
            validate_table_name("123table")


@pytest.mark.unit
class TestValidateDimension:
    """Tests for validate_dimension function."""

    def test_valid_dimensions(self):
        """Test that positive integers pass validation."""
        for dim in [1, 10, 100, 1000]:
            validate_dimension(dim)  # Should not raise

    def test_zero_dimension(self):
        """Test that zero dimension raises error."""
        with pytest.raises(ValidationError, match="positive integer"):
            validate_dimension(0)

    def test_negative_dimension(self):
        """Test that negative dimension raises error."""
        with pytest.raises(ValidationError, match="positive integer"):
            validate_dimension(-1)


@pytest.mark.unit
class TestValidateTopK:
    """Tests for validate_top_k function."""

    def test_valid_top_k(self):
        """Test that positive integers pass validation."""
        for k in [1, 5, 10, 100]:
            validate_top_k(k)  # Should not raise

    def test_zero_top_k(self):
        """Test that zero top_k raises error."""
        with pytest.raises(ValidationError, match="positive integer"):
            validate_top_k(0)

    def test_negative_top_k(self):
        """Test that negative top_k raises error."""
        with pytest.raises(ValidationError, match="positive integer"):
            validate_top_k(-1)


@pytest.mark.unit
class TestValidateLimit:
    """Tests for validate_limit function."""

    def test_valid_limit(self):
        """Test that positive integers pass validation."""
        for limit in [1, 10, 50, 100]:
            validate_limit(limit)  # Should not raise

    def test_zero_limit(self):
        """Test that zero limit raises error."""
        with pytest.raises(ValidationError, match="positive integer"):
            validate_limit(0)

    def test_negative_limit(self):
        """Test that negative limit raises error."""
        with pytest.raises(ValidationError, match="positive integer"):
            validate_limit(-1)


@pytest.mark.unit
class TestValidateOffset:
    """Tests for validate_offset function."""

    def test_valid_offset(self):
        """Test that non-negative integers pass validation."""
        for offset in [0, 1, 10, 100]:
            validate_offset(offset)  # Should not raise

    def test_negative_offset(self):
        """Test that negative offset raises error."""
        with pytest.raises(ValidationError, match="non-negative integer"):
            validate_offset(-1)


@pytest.mark.unit
class TestValidateEmbeddingsMatch:
    """Tests for validate_embeddings_match function."""

    def test_matching_lengths(self):
        """Test that matching lengths pass validation."""
        texts = ["a", "b", "c"]
        embeddings = [[1.0], [2.0], [3.0]]
        metadata = [{"x": 1}, {"x": 2}, {"x": 3}]
        validate_embeddings_match(texts, embeddings, metadata)  # Should not raise

    def test_matching_without_metadata(self):
        """Test validation without metadata."""
        texts = ["a", "b"]
        embeddings = [[1.0], [2.0]]
        validate_embeddings_match(texts, embeddings)  # Should not raise

    def test_mismatched_texts_embeddings(self):
        """Test that mismatched texts and embeddings raise error."""
        texts = ["a", "b"]
        embeddings = [[1.0]]
        with pytest.raises(ValidationError, match="must match"):
            validate_embeddings_match(texts, embeddings)

    def test_mismatched_texts_metadata(self):
        """Test that mismatched texts and metadata raise error."""
        texts = ["a", "b"]
        embeddings = [[1.0], [2.0]]
        metadata = [{"x": 1}]
        with pytest.raises(ValidationError, match="must match"):
            validate_embeddings_match(texts, embeddings, metadata)


@pytest.mark.unit
class TestValidateEmbeddingDimension:
    """Tests for validate_embedding_dimension function."""

    def test_matching_dimension(self):
        """Test that matching dimension passes validation."""
        embedding = [1.0, 2.0, 3.0]
        validate_embedding_dimension(embedding, 3)  # Should not raise

    def test_mismatched_dimension(self):
        """Test that mismatched dimension raises error."""
        embedding = [1.0, 2.0]
        with pytest.raises(DimensionMismatchError, match="does not match"):
            validate_embedding_dimension(embedding, 3)
