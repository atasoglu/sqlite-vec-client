"""Batch operations example for sqlite-vec-client.

Demonstrates:
- Bulk insert
- Batch retrieval
- Pagination
- Bulk update
- Bulk delete
- Transaction management
- Memory-efficient iteration
"""

from sqlite_vec_client import SQLiteVecClient


def main():
    client = SQLiteVecClient(table="products", db_path=":memory:")
    client.create_table(dim=64, distance="L2")

    # Bulk insert
    num_products = 100
    texts = [f"Product {i} description" for i in range(num_products)]
    embeddings = [[float(i % 10) / 10] * 64 for i in range(num_products)]
    metadata = [{"product_id": i, "price": i * 10} for i in range(num_products)]

    rowids = client.add(texts=texts, embeddings=embeddings, metadata=metadata)
    print(f"Inserted {len(rowids)} products")

    # Pagination - list first page
    page_size = 10
    page_1 = client.list_results(limit=page_size, offset=0, order="asc")
    print(f"\nPage 1 ({len(page_1)} items):")
    for rowid, text, meta, _ in page_1[:3]:
        print(f"  [{rowid}] {text} - ${meta['price']}")

    # Pagination - list second page
    page_2 = client.list_results(limit=page_size, offset=page_size, order="asc")
    print(f"\nPage 2 ({len(page_2)} items):")
    for rowid, text, meta, _ in page_2[:3]:
        print(f"  [{rowid}] {text} - ${meta['price']}")

    # Batch retrieval
    selected_ids = rowids[10:15]
    selected_products = client.get_many(selected_ids)
    print(f"\nRetrieved {len(selected_products)} specific products")

    # Bulk update
    updates = [
        (rowids[0], "Updated Product 0", {"price": 999}, None),
        (rowids[1], "Updated Product 1", {"price": 888}, None),
        (rowids[2], None, {"price": 777}, None),  # Only update metadata
    ]
    updated_count = client.update_many(updates)
    print(f"\nUpdated {updated_count} products")

    # Transaction example - atomic operations
    print("\nPerforming atomic transaction...")
    with client.transaction():
        new_texts = [f"New Product {i}" for i in range(5)]
        new_embeddings = [[0.5] * 64 for _ in range(5)]
        client.add(texts=new_texts, embeddings=new_embeddings)
        client.delete_many(rowids[50:55])
    print(f"Transaction completed. Total products: {client.count()}")

    # Memory-efficient iteration over all records
    print("\nIterating over all products (first 5):")
    for i, (rowid, text, meta, _) in enumerate(client.get_all(batch_size=20)):
        if i >= 5:
            break
        print(f"  [{rowid}] {text}")

    # Bulk delete
    to_delete = rowids[:20]
    deleted_count = client.delete_many(to_delete)
    print(f"\nDeleted {deleted_count} products")
    print(f"Remaining products: {client.count()}")

    client.close()


if __name__ == "__main__":
    main()
