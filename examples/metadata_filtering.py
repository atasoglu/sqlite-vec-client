"""Metadata filtering example for sqlite-vec-client.

Demonstrates:
- Adding records with metadata
- Querying records with get_all
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

    # Query all articles and filter by author
    print("\nAlice's articles:")
    for rowid, text, meta, _ in client.get_all():
        if meta.get("author") == "Alice":
            print(f"  [{rowid}] {text} - {meta}")

    # Query all articles and filter by text
    print("\nPython-related articles:")
    for rowid, text, meta, _ in client.get_all():
        if "Python" in text:
            print(f"  [{rowid}] {text}")

    # Update metadata
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
        updated = client.get(rowids[0])
        if updated:
            print(f"\nUpdated metadata: {updated[2]}")

    client.close()


if __name__ == "__main__":
    main()
