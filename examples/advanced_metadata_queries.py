"""Advanced metadata querying examples for sqlite-vec-client.

Demonstrates:
- Nested JSON path queries
- Complex filtering scenarios
- Performance comparison: filter vs manual iteration
- Real-world use cases
"""

from sqlite_vec_client import SQLiteVecClient


def main():
    client = SQLiteVecClient(table="documents", db_path=":memory:")
    client.create_table(dim=128, distance="cosine")

    # Add documents with nested metadata
    texts = [
        "Introduction to Python",
        "Advanced JavaScript",
        "Python for Data Science",
        "Java Programming Guide",
        "Machine Learning with Python",
    ]

    embeddings = [[0.1 * i] * 128 for i in range(len(texts))]

    metadata = [
        {"author": {"name": "Alice", "country": "US"}, "tags": ["python", "beginner"]},
        {
            "author": {"name": "Bob", "country": "UK"},
            "tags": ["javascript", "advanced"],
        },
        {"author": {"name": "Alice", "country": "US"}, "tags": ["python", "data"]},
        {"author": {"name": "Charlie", "country": "CA"}, "tags": ["java", "beginner"]},
        {"author": {"name": "Alice", "country": "US"}, "tags": ["python", "ml"]},
    ]

    rowids = client.add(texts=texts, embeddings=embeddings, metadata=metadata)
    print(f"Added {len(rowids)} documents\n")

    # Example 1: Nested JSON path queries
    print("=== Nested JSON Path Queries ===")
    print("\nDocuments by Alice (nested path):")
    results = client.filter_by_metadata({"author.name": "Alice"})
    for rowid, text, meta, _ in results:
        print(f"  [{rowid}] {text}")
    print(f"Total: {len(results)} documents")

    # Example 2: Filter by country
    print("\n\nDocuments from US authors:")
    results = client.filter_by_metadata({"author.country": "US"})
    for rowid, text, meta, _ in results:
        print(f"  [{rowid}] {text} by {meta['author']['name']}")

    # Example 3: Count by author
    print("\n\n=== Count by Author ===")
    for author in ["Alice", "Bob", "Charlie"]:
        count = client.count_by_metadata({"author.name": author})
        print(f"  {author}: {count} documents")

    # Example 4: Combined similarity + metadata filtering
    print("\n\n=== Combined Similarity + Metadata Filtering ===")
    query_emb = [0.15] * 128
    print("\nSimilar documents by Alice (top 10 candidates, filtered):")
    hits = client.similarity_search_with_filter(
        embedding=query_emb, filters={"author.name": "Alice"}, top_k=10
    )
    if hits:
        for rowid, text, distance in hits:
            dist_str = f"{distance:.4f}" if distance is not None else "N/A"
            print(f"  [{rowid}] {text} (distance: {dist_str})")
    else:
        print("  No results found (filters may be too restrictive)")

    # Example 5: Pagination for large result sets
    print("\n\n=== Pagination Example ===")
    all_us_docs = client.count_by_metadata({"author.country": "US"})
    print(f"Total US documents: {all_us_docs}")
    print("\nFetching in pages of 2:")
    for page in range(0, all_us_docs, 2):
        results = client.filter_by_metadata(
            {"author.country": "US"}, limit=2, offset=page
        )
        print(f"  Page {page//2 + 1}: {[r[1] for r in results]}")

    # Example 6: Alternative - regular similarity search
    print("\n\n=== Regular Similarity Search (no filter) ===")
    hits = client.similarity_search(embedding=query_emb, top_k=3)
    print("Top 3 similar documents:")
    for rowid, text, distance in hits:
        if distance is not None:
            print(f"  [{rowid}] {text} (distance: {distance:.4f})")
        else:
            print(f"  [{rowid}] {text}")

    # Performance note
    print("\n\n=== Performance Note ===")
    print("filter_by_metadata() uses SQLite's json_extract() for efficient queries.")
    print("This is much faster than manually iterating with get_all().")
    print("\nFor frequently queried fields, consider:")
    print("  1. Using filter_by_metadata() for ad-hoc queries")
    print("  2. Creating computed columns for indexed queries (advanced)")

    client.close()


if __name__ == "__main__":
    main()
