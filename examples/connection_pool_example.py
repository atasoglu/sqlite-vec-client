"""Example demonstrating connection pooling for concurrent access."""

import concurrent.futures
import time

from sqlite_vec_client import ConnectionPool, SQLiteVecClient


def worker_task(worker_id: int, pool: ConnectionPool) -> tuple[int, float]:
    """Simulate a worker performing database operations.

    Args:
        worker_id: Worker identifier
        pool: Connection pool to use

    Returns:
        Tuple of (worker_id, execution_time)
    """
    start = time.time()

    # Create client with pooled connection (no db_path needed)
    client = SQLiteVecClient(table=f"docs_{worker_id}", pool=pool)

    # Create table if needed
    client.create_table(dim=384)

    # Add some data
    texts = [f"Document {i} from worker {worker_id}" for i in range(10)]
    embeddings = [[0.1 * i] * 384 for i in range(10)]
    client.add(texts, embeddings)

    # Perform similarity search
    query = [0.5] * 384
    _ = client.similarity_search(query, top_k=5)

    # Close (returns connection to pool)
    client.close()

    elapsed = time.time() - start
    return worker_id, elapsed


def main() -> None:
    """Demonstrate connection pooling with concurrent workers."""
    print("Connection Pooling Example")
    print("=" * 50)

    # Create connection pool
    pool = ConnectionPool(
        connection_factory=lambda: SQLiteVecClient.create_connection("./pooled.db"),
        pool_size=5,
    )

    print("Created connection pool with size=5\n")

    # Run concurrent workers
    num_workers = 10
    print(f"Running {num_workers} concurrent workers...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_task, i, pool) for i in range(num_workers)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Print results
    print("\nWorker execution times:")
    for worker_id, elapsed in sorted(results):
        print(f"  Worker {worker_id}: {elapsed:.3f}s")

    avg_time = sum(t for _, t in results) / len(results)
    print(f"\nAverage execution time: {avg_time:.3f}s")

    # Cleanup
    pool.close_all()
    print("\nPool closed successfully")


if __name__ == "__main__":
    main()
