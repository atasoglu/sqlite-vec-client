"""Utility functions for benchmarking."""

import time
from typing import Any


def generate_embeddings(count: int, dim: int) -> list[list[float]]:
    """Generate dummy embeddings."""
    return [[float(i % 100) / 100.0] * dim for i in range(count)]


def generate_texts(count: int) -> list[str]:
    """Generate dummy texts."""
    return [f"document_{i}" for i in range(count)]


def generate_metadata(count: int) -> list[dict]:
    """Generate dummy metadata."""
    return [{"id": i, "category": f"cat_{i % 10}"} for i in range(count)]


def benchmark_operation(func, *args, **kwargs) -> tuple[float, Any]:
    """Measure execution time of an operation."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed, result
