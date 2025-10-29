"""Benchmark suite runner."""

import os
import tempfile
from typing import Any

from sqlite_vec_client import SQLiteVecClient

from .operations import (
    benchmark_add,
    benchmark_delete_many,
    benchmark_get_all,
    benchmark_get_many,
    benchmark_similarity_search,
    benchmark_update_many,
)
from .utils import generate_embeddings, generate_metadata, generate_texts


def run_benchmark_suite(
    dataset_size: int, config: dict[str, Any], db_mode: str = "file"
) -> list[dict]:
    """Run complete benchmark suite for a given dataset size."""
    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = (
            ":memory:" if db_mode == "memory" else os.path.join(tmpdir, "benchmark.db")
        )
        client = SQLiteVecClient(table="benchmark", db_path=db_path)

        try:
            # Create table
            dim = config["dimension"]
            distance = config["distance"]
            client.create_table(dim=dim, distance=distance)

            # Generate data
            texts = generate_texts(dataset_size)
            embeddings = generate_embeddings(dataset_size, dim)
            metadata = generate_metadata(dataset_size)

            # Benchmark: Add
            print(f"  Benchmarking add ({dataset_size} records)...")
            results.append(benchmark_add(client, texts, embeddings, metadata))

            # Get rowids for subsequent operations
            rowids = list(range(1, dataset_size + 1))

            # Benchmark: Get Many
            print(f"  Benchmarking get_many ({dataset_size} records)...")
            results.append(benchmark_get_many(client, rowids))

            # Benchmark: Similarity Search
            print("  Benchmarking similarity_search...")
            query_emb = [0.5] * dim
            iterations = config["similarity_search"]["iterations"]
            for top_k in config["similarity_search"]["top_k_values"]:
                results.append(
                    benchmark_similarity_search(client, query_emb, top_k, iterations)
                )

            # Benchmark: Update Many
            print(f"  Benchmarking update_many ({dataset_size} records)...")
            new_texts = [f"updated_{i}" for i in range(dataset_size)]
            results.append(benchmark_update_many(client, rowids, new_texts))

            # Benchmark: Get All
            print(f"  Benchmarking get_all ({dataset_size} records)...")
            batch_size = config["batch_size"]
            results.append(benchmark_get_all(client, dataset_size, batch_size))

            # Benchmark: Delete Many
            print(f"  Benchmarking delete_many ({dataset_size} records)...")
            results.append(benchmark_delete_many(client, rowids))
        finally:
            client.close()

    return results
