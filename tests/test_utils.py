"""Unit tests for utility functions."""

import pytest

from sqlite_vec_client.utils import deserialize_f32, serialize_f32


@pytest.mark.unit
class TestSerializeF32:
    """Tests for serialize_f32 function."""

    def test_serialize_empty_list(self):
        """Test serialization of empty list."""
        result = serialize_f32([])
        assert result == b""

    def test_serialize_single_value(self):
        """Test serialization of single float."""
        result = serialize_f32([1.0])
        assert isinstance(result, bytes)
        assert len(result) == 4  # 4 bytes per float32

    def test_serialize_multiple_values(self):
        """Test serialization of multiple floats."""
        embeddings = [0.1, 0.2, 0.3]
        result = serialize_f32(embeddings)
        assert isinstance(result, bytes)
        assert len(result) == 12  # 3 floats * 4 bytes

    def test_serialize_negative_values(self):
        """Test serialization handles negative values."""
        embeddings = [-1.0, -2.5, -3.7]
        result = serialize_f32(embeddings)
        assert isinstance(result, bytes)
        assert len(result) == 12


@pytest.mark.unit
class TestDeserializeF32:
    """Tests for deserialize_f32 function."""

    def test_deserialize_empty_bytes(self):
        """Test deserialization of empty bytes."""
        result = deserialize_f32(b"")
        assert result == []

    def test_deserialize_single_value(self):
        """Test deserialization of single float."""
        serialized = serialize_f32([1.0])
        result = deserialize_f32(serialized)
        assert len(result) == 1
        assert pytest.approx(result[0]) == 1.0

    def test_deserialize_multiple_values(self):
        """Test deserialization of multiple floats."""
        original = [0.1, 0.2, 0.3]
        serialized = serialize_f32(original)
        result = deserialize_f32(serialized)
        assert len(result) == 3
        assert pytest.approx(result) == original

    def test_roundtrip(self):
        """Test serialize -> deserialize roundtrip."""
        original = [1.5, -2.7, 3.14159, 0.0, -0.5]
        serialized = serialize_f32(original)
        deserialized = deserialize_f32(serialized)
        assert pytest.approx(deserialized) == original
