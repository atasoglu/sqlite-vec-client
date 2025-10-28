"""Context manager example for sqlite-vec-client.

Demonstrates:
- Using client as context manager
- Automatic connection cleanup
- Exception handling
"""

from sqlite_vec_client import SQLiteVecClient


def main():
    # Using context manager - connection closes automatically
    with SQLiteVecClient(table="notes", db_path=":memory:") as client:
        client.create_table(dim=256, distance="cosine")

        texts = ["First note", "Second note", "Third note"]
        embeddings = [[0.1] * 256, [0.2] * 256, [0.3] * 256]

        rowids = client.add(texts=texts, embeddings=embeddings)
        print(f"Added {len(rowids)} notes")

        # Search
        results = client.similarity_search(embedding=[0.15] * 256, top_k=2)
        print("\nTop 2 similar notes:")
        for rowid, text, distance in results:
            print(f"  [{rowid}] {text} (distance: {distance:.4f})")

    # Connection is automatically closed here
    print("\nConnection closed automatically")

    # Exception handling with context manager
    try:
        with SQLiteVecClient(table="temp", db_path=":memory:") as client:
            client.create_table(dim=128, distance="cosine")
            # Simulate error
            raise ValueError("Simulated error")
    except ValueError as e:
        print(f"\nHandled error: {e}")
        print("Connection still closed properly despite exception")


if __name__ == "__main__":
    main()
