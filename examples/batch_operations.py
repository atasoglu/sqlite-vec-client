"""Batch operations example for sqlite-vec-client.

Demonstrates:
- Bulk insert
- Batch retrieval
- Pagination
- Bulk delete
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

    # Bulk delete
    to_delete = rowids[:20]
    deleted_count = client.delete_many(to_delete)
    print(f"\nDeleted {deleted_count} products")
    print(f"Remaining products: {client.count()}")

    client.close()


if __name__ == "__main__":
    main()
