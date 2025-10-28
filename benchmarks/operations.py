"""Benchmark operations for CRUD methods."""

import statistics
import time

from sqlite_vec_client import SQLiteVecClient

from .utils import benchmark_operation


def benchmark_add(
    client: SQLiteVecClient,
    texts: list[str],
    embeddings: list[list[float]],
    metadata: list[dict],
) -> dict:
    """Benchmark add operations."""
    elapsed, rowids = benchmark_operation(
        client.add, texts=texts, embeddings=embeddings, metadata=metadata
    )
    return {
        "operation": "add",
        "count": len(texts),
        "time": elapsed,
        "ops_per_sec": len(texts) / elapsed,
    }


def benchmark_get_many(client: SQLiteVecClient, rowids: list[int]) -> dict:
    """Benchmark get_many operations."""
    elapsed, _ = benchmark_operation(client.get_many, rowids)
    return {
        "operation": "get_many",
        "count": len(rowids),
        "time": elapsed,
        "ops_per_sec": len(rowids) / elapsed,
    }


def benchmark_similarity_search(
    client: SQLiteVecClient, embedding: list[float], top_k: int, iterations: int
) -> dict:
    """Benchmark similarity search operations."""
    times = []
    for _ in range(iterations):
        elapsed, _ = benchmark_operation(
            client.similarity_search, embedding=embedding, top_k=top_k
        )
        times.append(elapsed)

    avg_time = statistics.mean(times)
    return {
        "operation": "similarity_search",
        "top_k": top_k,
        "iterations": iterations,
        "avg_time": avg_time,
        "min_time": min(times),
        "max_time": max(times),
        "searches_per_sec": 1 / avg_time,
    }


def benchmark_update_many(
    client: SQLiteVecClient, rowids: list[int], texts: list[str]
) -> dict:
    """Benchmark update_many operations."""
    updates = [(rid, text, None, None) for rid, text in zip(rowids, texts)]
    elapsed, count = benchmark_operation(client.update_many, updates)
    return {
        "operation": "update_many",
        "count": count,
        "time": elapsed,
        "ops_per_sec": count / elapsed,
    }


def benchmark_delete_many(client: SQLiteVecClient, rowids: list[int]) -> dict:
    """Benchmark delete_many operations."""
    elapsed, count = benchmark_operation(client.delete_many, rowids)
    return {
        "operation": "delete_many",
        "count": count,
        "time": elapsed,
        "ops_per_sec": count / elapsed,
    }


def benchmark_get_all(
    client: SQLiteVecClient, expected_count: int, batch_size: int
) -> dict:
    """Benchmark get_all operations."""

    start = time.perf_counter()
    count = sum(1 for _ in client.get_all(batch_size=batch_size))
    elapsed = time.perf_counter() - start
    return {
        "operation": "get_all",
        "count": count,
        "time": elapsed,
        "ops_per_sec": count / elapsed,
    }
