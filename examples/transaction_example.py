"""Transaction example for sqlite-vec-client.

Demonstrates:
- Atomic transactions with context manager
- All CRUD operations in a single transaction
- Rollback on error
- Transaction isolation
"""

from sqlite_vec_client import SQLiteVecClient


def main():
    client = SQLiteVecClient(table="products", db_path=":memory:")
    client.create_table(dim=64, distance="cosine")

    # Example 1: Successful transaction with all CRUD operations
    print("Example 1: Successful transaction")
    print("-" * 50)

    with client.transaction():
        # CREATE: Add initial products
        texts = [f"Product {i}" for i in range(5)]
        embeddings = [[float(i)] * 64 for i in range(5)]
        metadata = [{"price": i * 10, "stock": 100} for i in range(5)]
        rowids = client.add(texts=texts, embeddings=embeddings, metadata=metadata)
        print(f"[+] Added {len(rowids)} products: {rowids}")

        # READ: Get a product
        product = client.get(rowids[0])
        if product:
            print(f"[+] Retrieved product {product[0]}: {product[1]}")

        # UPDATE: Update single product
        updated = client.update(
            rowids[0], text="Updated Product 0", metadata={"price": 99}
        )
        print(f"[+] Updated product {rowids[0]}: {updated}")

        # UPDATE: Bulk update
        updates = [
            (rowids[1], "Bulk Updated 1", {"price": 150}, None),
            (rowids[2], None, {"price": 200, "stock": 50}, None),
        ]
        count = client.update_many(updates)
        print(f"[+] Bulk updated {count} products")

        # DELETE: Delete single product
        deleted = client.delete(rowids[3])
        print(f"[+] Deleted product {rowids[3]}: {deleted}")

        # DELETE: Bulk delete
        deleted_count = client.delete_many([rowids[4]])
        print(f"[+] Bulk deleted {deleted_count} products")

    # Transaction committed - verify results
    print("\n[+] Transaction committed successfully")
    print(f"  Total products remaining: {client.count()}")

    # Example 2: Failed transaction with rollback
    print("\n\nExample 2: Failed transaction (rollback)")
    print("-" * 50)

    initial_count = client.count()
    print(f"Initial count: {initial_count}")

    try:
        with client.transaction():
            # Add more products
            new_texts = ["New Product 1", "New Product 2"]
            new_embeddings = [[1.0] * 64, [2.0] * 64]
            new_rowids = client.add(texts=new_texts, embeddings=new_embeddings)
            print(f"[+] Added {len(new_rowids)} products: {new_rowids}")

            # Update existing
            client.update(rowids[0], text="This will be rolled back")
            print(f"[+] Updated product {rowids[0]}")

            # Simulate error
            raise ValueError("Simulated error - transaction will rollback")

    except ValueError as e:
        print(f"\n[-] Error occurred: {e}")
        print("[+] Transaction rolled back automatically")

    # Verify rollback
    final_count = client.count()
    print(f"  Final count: {final_count}")
    print(f"  Count unchanged: {initial_count == final_count}")

    # Verify data not changed
    product = client.get(rowids[0])
    if product:
        print(f"  Product {rowids[0]} text: {product[1]}")

    # Example 3: Nested operations with similarity search
    print("\n\nExample 3: Complex transaction with search")
    print("-" * 50)

    with client.transaction():
        # Add products with similar embeddings
        similar_texts = ["Red Apple", "Green Apple", "Orange"]
        similar_embeddings = [
            [0.9, 0.1] + [0.0] * 62,
            [0.85, 0.15] + [0.0] * 62,
            [0.5, 0.5] + [0.0] * 62,
        ]
        similar_rowids = client.add(texts=similar_texts, embeddings=similar_embeddings)
        print(f"[+] Added {len(similar_rowids)} products")

        # Search within transaction
        query_emb = [0.9, 0.1] + [0.0] * 62
        results = client.similarity_search(embedding=query_emb, top_k=2)
        print(f"[+] Found {len(results)} similar products:")
        for rowid, text, distance in results:
            dist_str = f"{distance:.4f}" if distance is not None else "N/A"
            print(f"    [{rowid}] {text} (distance: {dist_str})")

        # Update based on search results
        for rowid, text, distance in results:
            if distance is not None and distance < 0.1:
                client.update(rowid, metadata={"featured": True})
                print(f"[+] Marked product {rowid} as featured")

    print("\n[+] Complex transaction completed")
    print(f"  Total products: {client.count()}")

    # Example 4: Batch operations in transaction
    print("\n\nExample 4: Large batch operations")
    print("-" * 50)

    with client.transaction():
        # Bulk insert
        batch_size = 20
        batch_texts = [f"Batch Product {i}" for i in range(batch_size)]
        batch_embeddings = [[float(i % 10)] * 64 for i in range(batch_size)]
        batch_rowids = client.add(texts=batch_texts, embeddings=batch_embeddings)
        print(f"[+] Bulk inserted {len(batch_rowids)} products")

        # Bulk update all
        bulk_updates = [
            (rid, None, {"batch": True, "processed": True}, None)
            for rid in batch_rowids[:10]
        ]
        updated = client.update_many(bulk_updates)
        print(f"[+] Bulk updated {updated} products")

        # Bulk delete some
        deleted = client.delete_many(batch_rowids[10:15])
        print(f"[+] Bulk deleted {deleted} products")

    print("\n[+] Batch operations completed")
    print(f"  Final total: {client.count()}")

    client.close()


if __name__ == "__main__":
    main()
