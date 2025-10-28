"""Benchmark suite for sqlite-vec-client."""

from .config_loader import load_config
from .operations import (
    benchmark_add,
    benchmark_delete_many,
    benchmark_get_all,
    benchmark_get_many,
    benchmark_similarity_search,
    benchmark_update_many,
)
from .reporter import export_to_csv, print_results, print_summary
from .runner import run_benchmark_suite
from .utils import generate_embeddings, generate_metadata, generate_texts

__all__ = [
    "load_config",
    "run_benchmark_suite",
    "print_results",
    "print_summary",
    "export_to_csv",
    "benchmark_add",
    "benchmark_get_many",
    "benchmark_similarity_search",
    "benchmark_update_many",
    "benchmark_get_all",
    "benchmark_delete_many",
    "generate_embeddings",
    "generate_texts",
    "generate_metadata",
]
