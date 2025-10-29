"""Export/import example for sqlite-vec-client.

Demonstrates:
- Exporting data to JSON and CSV
- Importing data from JSON and CSV
- Filtered exports
- Backup and restore workflows
"""

from sqlite_vec_client import SQLiteVecClient


def main():
    # Create and populate database
    client = SQLiteVecClient(table="documents", db_path=":memory:")
    client.create_table(dim=128, distance="cosine")

    texts = [
        "Introduction to Python",
        "Advanced JavaScript",
        "Python for Data Science",
        "Java Programming Guide",
        "Machine Learning with Python",
    ]

    embeddings = [[0.1 * i] * 128 for i in range(len(texts))]

    metadata = [
        {"category": "python", "level": "beginner"},
        {"category": "javascript", "level": "advanced"},
        {"category": "python", "level": "intermediate"},
        {"category": "java", "level": "beginner"},
        {"category": "python", "level": "advanced"},
    ]

    client.add(texts=texts, embeddings=embeddings, metadata=metadata)
    print(f"Added {client.count()} documents\n")

    # Example 1: Export all data to JSON
    print("=== Export to JSON ===")
    count = client.export_to_json("backup.jsonl")
    print(f"Exported {count} records to backup.jsonl\n")

    # Example 2: Export filtered data to JSON
    print("=== Export Filtered Data ===")
    count = client.export_to_json("python_docs.jsonl", filters={"category": "python"})
    print(f"Exported {count} Python documents to python_docs.jsonl\n")

    # Example 3: Export to CSV (without embeddings for readability)
    print("=== Export to CSV ===")
    count = client.export_to_csv("documents.csv", include_embeddings=False)
    print(f"Exported {count} records to documents.csv\n")

    # Example 4: Export to CSV with embeddings
    print("=== Export to CSV with Embeddings ===")
    count = client.export_to_csv("documents_full.csv", include_embeddings=True)
    print(f"Exported {count} records with embeddings to documents_full.csv\n")

    # Example 5: Backup and restore workflow
    print("=== Backup and Restore Workflow ===")

    # Backup
    print("Creating backup...")
    client.export_to_json("backup_full.jsonl")

    # Simulate data loss
    print("Simulating data loss...")
    original_count = client.count()
    for rowid in range(1, original_count + 1):
        client.delete(rowid)
    print(f"Records after deletion: {client.count()}")

    # Restore
    print("Restoring from backup...")
    count = client.import_from_json("backup_full.jsonl")
    print(f"Restored {count} records")
    print(f"Records after restore: {client.count()}\n")

    # Example 6: Data migration scenario
    print("=== Data Migration Scenario ===")

    # Export from source
    print("Exporting from source database...")
    client.export_to_json("migration.jsonl")

    # Import to new database (simulated with same client)
    print("Importing to destination database...")
    # In real scenario, you would create a new client with different db_path
    # new_client = SQLiteVecClient(table="documents", db_path="new.db")
    # new_client.create_table(dim=128)
    # new_client.import_from_json("migration.jsonl")
    print("Migration complete!\n")

    # Example 7: Filtered export for data sharing
    print("=== Export Subset for Sharing ===")
    count = client.export_to_csv(
        "beginner_docs.csv", include_embeddings=False, filters={"level": "beginner"}
    )
    print(f"Exported {count} beginner-level documents for sharing\n")

    # Cleanup
    print("=== Cleanup ===")
    import os

    for file in [
        "backup.jsonl",
        "python_docs.jsonl",
        "documents.csv",
        "documents_full.csv",
        "backup_full.jsonl",
        "migration.jsonl",
        "beginner_docs.csv",
    ]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed {file}")

    client.close()
    print("\nExample complete!")


if __name__ == "__main__":
    main()
