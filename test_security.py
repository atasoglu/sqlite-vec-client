"""Quick test to verify security and error handling improvements."""

import tempfile
from pathlib import Path

from sqlite_vec_client import (
    SQLiteVecClient,
    TableNameError,
    TableNotFoundError,
    ValidationError,
)


def test_table_name_validation():
    """Test that invalid table names are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")

        # Valid table names should work
        client = SQLiteVecClient(table="valid_table", db_path=db_path)
        client.close()

        # Invalid table names should raise TableNameError
        try:
            SQLiteVecClient(table="invalid-table", db_path=db_path)
            assert False, "Should have raised TableNameError"
        except TableNameError as e:
            print(f"[OK] Caught invalid table name: {e}")

        try:
            SQLiteVecClient(table="123invalid", db_path=db_path)
            assert False, "Should have raised TableNameError"
        except TableNameError as e:
            print(f"[OK] Caught invalid table name: {e}")

        try:
            SQLiteVecClient(table="table; DROP TABLE users;", db_path=db_path)
            assert False, "Should have raised TableNameError"
        except TableNameError as e:
            print(f"[OK] Caught SQL injection attempt: {e}")


def test_input_validation():
    """Test that invalid inputs are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)

        # Invalid dimension
        try:
            client.create_table(dim=-1)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            print(f"[OK] Caught invalid dimension: {e}")

        try:
            client.create_table(dim=0)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            print(f"[OK] Caught invalid dimension: {e}")

        client.create_table(dim=3)

        # Invalid top_k
        try:
            client.similarity_search(embedding=[0.1, 0.2, 0.3], top_k=0)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            print(f"[OK] Caught invalid top_k: {e}")

        # Invalid limit
        try:
            client.list_results(limit=-1)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            print(f"[OK] Caught invalid limit: {e}")

        # Invalid offset
        try:
            client.list_results(offset=-1)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            print(f"[OK] Caught invalid offset: {e}")

        # Mismatched texts and embeddings
        try:
            client.add(texts=["a", "b"], embeddings=[[0.1, 0.2, 0.3]])
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            print(f"[OK] Caught mismatched lists: {e}")

        client.close()


def test_table_not_found():
    """Test that operations on non-existent tables raise TableNotFoundError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        client = SQLiteVecClient(table="test", db_path=db_path)

        # Try to search without creating table
        try:
            client.similarity_search(embedding=[0.1, 0.2, 0.3])
            assert False, "Should have raised TableNotFoundError"
        except TableNotFoundError as e:
            print(f"[OK] Caught table not found: {e}")

        # Try to add without creating table
        try:
            client.add(texts=["test"], embeddings=[[0.1, 0.2, 0.3]])
            assert False, "Should have raised TableNotFoundError"
        except TableNotFoundError as e:
            print(f"[OK] Caught table not found: {e}")

        client.close()


if __name__ == "__main__":
    print("Testing table name validation...")
    test_table_name_validation()
    print("\nTesting input validation...")
    test_input_validation()
    print("\nTesting table not found errors...")
    test_table_not_found()
    print("\n[SUCCESS] All security tests passed!")
