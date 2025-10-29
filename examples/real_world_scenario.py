"""Real-world scenario: Document search system.

Demonstrates a practical use case:
- Building a searchable document database
- Semantic search with embeddings
- CRUD operations
- Metadata filtering
"""

import random

from sqlite_vec_client import SQLiteVecClient


def generate_mock_embedding(dim: int, seed: int) -> list[float]:
    """Generate a mock embedding for demonstration."""
    random.seed(seed)
    return [random.random() for _ in range(dim)]


def main():
    # Initialize document search system
    with SQLiteVecClient(table="knowledge_base", db_path=":memory:") as client:
        client.create_table(dim=384, distance="cosine")

        # Add documents to knowledge base
        documents = [
            {
                "text": "Python is a programming language known for its simplicity",
                "metadata": {
                    "category": "programming",
                    "language": "python",
                    "difficulty": "beginner",
                },
            },
            {
                "text": "Machine learning models require large datasets for training",
                "metadata": {
                    "category": "ai",
                    "language": "general",
                    "difficulty": "intermediate",
                },
            },
            {
                "text": "SQLite is a lightweight embedded database engine",
                "metadata": {
                    "category": "database",
                    "language": "sql",
                    "difficulty": "beginner",
                },
            },
            {
                "text": "Neural networks consist of layers of interconnected nodes",
                "metadata": {
                    "category": "ai",
                    "language": "general",
                    "difficulty": "advanced",
                },
            },
            {
                "text": "Vector databases enable semantic search capabilities",
                "metadata": {
                    "category": "database",
                    "language": "general",
                    "difficulty": "intermediate",
                },
            },
        ]

        texts = [doc["text"] for doc in documents]
        metadata = [doc["metadata"] for doc in documents]
        embeddings = [generate_mock_embedding(384, i) for i in range(len(documents))]

        rowids = client.add(texts=texts, embeddings=embeddings, metadata=metadata)
        print(f"Indexed {len(rowids)} documents in knowledge base\n")

        # Semantic search: Find documents about databases
        print("Search: 'database systems'")
        query_emb = generate_mock_embedding(384, 42)
        results = client.similarity_search(embedding=query_emb, top_k=3)

        print("Top 3 results:")
        for i, (rowid, text, distance) in enumerate(results, 1):
            record = client.get(rowid)
            if record:
                _, _, meta, _ = record
                print(f"  {i}. [{meta['category']}] {text[:60]}...")
                print(
                    f"     Distance: {distance:.4f}, Difficulty: {meta['difficulty']}\n"
                )

        # Filter by category using get_all
        print("All AI-related documents (intermediate):")
        for rowid, text, meta, _ in client.get_all():
            if (
                meta.get("category") == "ai"
                and meta.get("difficulty") == "intermediate"
            ):
                print(f"  • {text[:60]}...")

        # Update document
        if rowids:
            client.update(
                rowids[0],
                metadata={
                    "category": "programming",
                    "language": "python",
                    "difficulty": "beginner",
                    "reviewed": True,
                },
            )
            print(f"\nUpdated document {rowids[0]}")

        # Statistics
        print("\nKnowledge base statistics:")
        print(f"  Total documents: {client.count()}")

        # List first 3 documents
        print("  First 3 documents:")
        for i, (rowid, text, _, _) in enumerate(client.get_all()):
            if i >= 3:
                break
            print(f"    [{rowid}] {text[:50]}...")


if __name__ == "__main__":
    main()
