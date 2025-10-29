"""Metadata filtering example for sqlite-vec-client.

Demonstrates:
- Adding records with metadata
- Filtering by metadata fields
- Counting records by metadata
- Combined similarity search with metadata filtering
- Updating metadata
"""

from sqlite_vec_client import SQLiteVecClient


def main():
    client = SQLiteVecClient(table="articles", db_path=":memory:")
    client.create_table(dim=128, distance="cosine")

    # Add articles with metadata
    texts = [
        "Introduction to Python programming",
        "Advanced machine learning techniques",
        "Python for data science",
    ]

    embeddings = [
        [0.1] * 128,
        [0.2] * 128,
        [0.15] * 128,
    ]

    metadata = [
        {"category": "programming", "author": "Alice", "year": 2023},
        {"category": "ai", "author": "Bob", "year": 2024},
        {"category": "data-science", "author": "Alice", "year": 2024},
    ]

    rowids = client.add(texts=texts, embeddings=embeddings, metadata=metadata)
    print(f"Added {len(rowids)} articles")

    # Filter by metadata - efficient JSON_EXTRACT queries
    print("\nAlice's articles (using filter_by_metadata):")
    results = client.filter_by_metadata({"author": "Alice"})
    for rowid, text, meta, _ in results:
        print(f"  [{rowid}] {text} - {meta}")

    # Filter by multiple fields
    print("\nArticles from 2024:")
    results = client.filter_by_metadata({"year": 2024})
    for rowid, text, meta, _ in results:
        print(f"  [{rowid}] {text} - Year: {meta['year']}")

    # Count records by metadata
    count = client.count_by_metadata({"author": "Alice"})
    print(f"\nTotal articles by Alice: {count}")

    # Combined similarity search with metadata filtering
    print("\nSimilar to 'Python' in category 'programming':")
    query_emb = [0.1] * 128
    hits = client.similarity_search_with_filter(
        embedding=query_emb, filters={"category": "programming"}, top_k=5
    )
    for rowid, text, distance in hits:
        print(f"  [{rowid}] {text} (distance: {distance:.4f})")

    # Update metadata and verify with filter
    if rowids:
        client.update(
            rowids[0],
            metadata={
                "category": "programming",
                "author": "Alice",
                "year": 2024,
                "updated": True,
            },
        )
        # Find updated records
        updated_records = client.filter_by_metadata({"updated": True})
        print(f"\nUpdated records: {len(updated_records)}")
        if updated_records:
            print(f"  Metadata: {updated_records[0][2]}")

    # Pagination example
    print("\nPagination example (limit=2):")
    page1 = client.filter_by_metadata({"year": 2024}, limit=2, offset=0)
    print(f"  Page 1: {len(page1)} results")

    client.close()


if __name__ == "__main__":
    main()
