"""Benchmark results reporting."""

import csv
import os
from datetime import datetime

from tabulate import tabulate  # type: ignore[import-untyped]


def print_results(results: list[dict], table_format: str):
    """Print benchmark results in a formatted table."""
    # Separate similarity_search results
    regular_results = [r for r in results if r["operation"] != "similarity_search"]
    search_results = [r for r in results if r["operation"] == "similarity_search"]

    # Get count from first result for header
    count = regular_results[0].get("count", 0) if regular_results else 0

    # Print CRUD operations table
    table_data = []
    for result in regular_results:
        op = result["operation"]
        time_val = result.get("time", 0)
        ops_per_sec = result.get("ops_per_sec", 0)
        table_data.append([op, f"{time_val:.4f}", f"{ops_per_sec:.2f}"])

    print(f"\nCRUD Operations (n={count:,}):")
    print(
        tabulate(
            table_data,
            headers=["Operation", "Time (s)", "Ops/sec"],
            tablefmt=table_format,
        )
    )

    # Print similarity search table separately
    if search_results:
        iterations = search_results[0].get("count", 0)
        search_data = []
        for result in search_results:
            top_k = result.get("top_k", "-")
            time_val = result.get("time", 0)
            ops_per_sec = result.get("ops_per_sec", 0)
            search_data.append([top_k, f"{time_val:.4f}", f"{ops_per_sec:.2f}"])

        print(f"\nSimilarity Search (iterations={iterations}):")
        print(
            tabulate(
                search_data,
                headers=["Top-K", "Time (s)", "Searches/sec"],
                tablefmt=table_format,
            )
        )


def print_summary(
    all_results: dict[str, dict[int, list[dict]]],
    dataset_sizes: list[int],
    table_format: str,
):
    """Print summary table of all benchmark results."""
    for db_mode, mode_results in all_results.items():
        print("\n" + "=" * 80)
        print(f"SUMMARY - Operations per Second by Dataset Size ({db_mode.upper()} DB)")
        print("=" * 80)

        operations = [
            "add",
            "get_many",
            "update_many",
            "get_all",
            "delete_many",
            "similarity_search",
        ]
        summary_data = []
        for op in operations:
            row = [op]
            for size in dataset_sizes:
                matching = [r for r in mode_results[size] if r["operation"] == op]
                if matching:
                    ops_per_sec = matching[0].get("ops_per_sec", 0)
                    row.append(f"{ops_per_sec:,.0f}")
                else:
                    row.append("N/A")
            summary_data.append(row)

        headers = ["Operation"] + [f"{s:,}" for s in dataset_sizes]
        print(tabulate(summary_data, headers=headers, tablefmt=table_format))
        print("=" * 80)


def export_to_csv(
    all_results: dict[str, dict[int, list[dict]]],
    dataset_sizes: list[int],
    output_dir: str,
):
    """Export benchmark results to CSV files."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for db_mode, mode_results in all_results.items():
        for size in dataset_sizes:
            filename = os.path.join(
                output_dir, f"benchmark_{db_mode}_{size}_{timestamp}.csv"
            )

            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Operation", "ops_per_sec", "time_sec"])

                operations = [
                    "add",
                    "get_many",
                    "update_many",
                    "get_all",
                    "delete_many",
                ]
                for op in operations:
                    matching = [r for r in mode_results[size] if r["operation"] == op]
                    if matching:
                        ops_per_sec = matching[0].get("ops_per_sec", 0)
                        time_val = matching[0].get("time", 0)
                        writer.writerow([op, f"{ops_per_sec:.2f}", f"{time_val:.4f}"])
                    else:
                        writer.writerow([op, "N/A", "N/A"])

                # Add similarity search results with top_k in operation name
                search_results = [
                    r
                    for r in mode_results[size]
                    if r["operation"] == "similarity_search"
                ]
                for result in search_results:
                    top_k = result.get("top_k", 0)
                    ops_per_sec = result.get("ops_per_sec", 0)
                    time_val = result.get("time", 0)
                    writer.writerow(
                        [
                            f"similarity_search_{top_k}",
                            f"{ops_per_sec:.2f}",
                            f"{time_val:.4f}",
                        ]
                    )

            print(f"Exported {db_mode} ({size} records) to: {filename}")
