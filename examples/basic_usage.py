"""Basic usage example for sqlite-vec-client.

Demonstrates:
- Creating a client and table
- Adding texts with embeddings
- Similarity search
- Retrieving records
"""

from sqlite_vec_client import SQLiteVecClient


def main():
    # Initialize client
    client = SQLiteVecClient(table="documents", db_path=":memory:")

    # Create table with 384-dimensional embeddings
    client.create_table(dim=384, distance="cosine")

    # Sample texts and embeddings (384-dim vectors)
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a subset of artificial intelligence",
        "Python is a popular programming language",
    ]

    embeddings = [
        [0.1, 0.2, 0.3] + [0.0] * 381,
        [0.5, 0.4, 0.3] + [0.0] * 381,
        [0.2, 0.1, 0.05] + [0.0] * 381,
    ]

    # Add records
    rowids = client.add(texts=texts, embeddings=embeddings)
    print(f"Added {len(rowids)} records: {rowids}")

    # Similarity search
    query_embedding = [0.1, 0.2, 0.3] + [0.0] * 381
    results = client.similarity_search(embedding=query_embedding, top_k=2)

    print("\nTop 2 similar documents:")
    for rowid, text, distance in results:
        print(f"  [{rowid}] {text[:50]}... (distance: {distance:.4f})")

    # Get record by ID
    record = client.get_by_id(rowids[0])
    if record:
        rowid, text, metadata, embedding = record
        print(f"\nRecord {rowid}: {text}")

    # Count total records
    print(f"\nTotal records: {client.count()}")

    client.close()


if __name__ == "__main__":
    main()
