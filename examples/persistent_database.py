"""Persistent database example for sqlite-vec-client.

Demonstrates:
- Creating a persistent .db file
- Loading from existing .db file
- Data persistence across sessions
"""

from sqlite_vec_client import SQLiteVecClient


def create_database():
    """Create and populate a persistent database."""
    print("Creating database...")
    client = SQLiteVecClient(table="documents", db_path="./my_vectors.db")
    client.create_table(dim=128, distance="cosine")

    texts = [
        "First document",
        "Second document",
        "Third document",
    ]
    embeddings = [[0.1] * 128, [0.2] * 128, [0.3] * 128]

    rowids = client.add(texts=texts, embeddings=embeddings)
    print(f"Added {len(rowids)} documents")
    print(f"Total records: {client.count()}")

    client.close()


def load_database():
    """Load and query existing database."""
    print("\nLoading existing database...")
    client = SQLiteVecClient(table="documents", db_path="./my_vectors.db")

    print(f"Total records: {client.count()}")

    # Search
    results = client.similarity_search(embedding=[0.15] * 128, top_k=2)
    print("\nTop 2 results:")
    for rowid, text, distance in results:
        print(f"  [{rowid}] {text} (distance: {distance:.4f})")

    client.close()


if __name__ == "__main__":
    create_database()
    load_database()
