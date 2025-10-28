"""Benchmark script for sqlite-vec-client CRUD operations.

Measures performance of all operations with varying dataset sizes.
"""

import argparse

from .config_loader import load_config
from .reporter import export_to_csv, print_results, print_summary
from .runner import run_benchmark_suite


def main():
    """Run benchmarks with different dataset sizes."""
    parser = argparse.ArgumentParser(description="Run sqlite-vec-client benchmarks")
    parser.add_argument("-c", "--config", type=str, help="Path to config YAML file")
    parser.add_argument(
        "-o", "--output", type=str, help="Output directory for CSV export"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    print("SQLite-Vec-Client Performance Benchmark")
    print("=" * 80)
    print(f"Configuration: dim={config['dimension']}, distance={config['distance']}")
    print("=" * 80)

    dataset_sizes = config["dataset_sizes"]
    table_format = config["table_format"]
    db_modes = config.get("db_modes", ["file"])
    all_results = {}

    for db_mode in db_modes:
        print(f"\n{'=' * 80}")
        print(f"Testing with {db_mode.upper()} database")
        print("=" * 80)

        mode_results = {}
        for size in dataset_sizes:
            print(f"\nRunning benchmark with {size:,} records...")
            results = run_benchmark_suite(size, config, db_mode)
            mode_results[size] = results
            print_results(results, table_format)

        all_results[db_mode] = mode_results

    print_summary(all_results, dataset_sizes, table_format)

    if args.output:
        export_to_csv(all_results, dataset_sizes, args.output)


if __name__ == "__main__":
    main()
