"""Benchmark results reporting."""

import csv
import os
from datetime import datetime

from tabulate import tabulate  # type: ignore[import-untyped]


def print_results(results: list[dict], table_format: str):
    """Print benchmark results in a formatted table."""
    table_data = []
    for result in results:
        op = result["operation"]
        if "top_k" in result:
            op = f"{op} (k={result['top_k']})"

        count = result.get("count", result.get("iterations", "-"))
        time_val = result.get("time", result.get("avg_time", 0))
        ops_per_sec = result.get("ops_per_sec", result.get("searches_per_sec", 0))

        table_data.append([op, count, f"{time_val:.4f}", f"{ops_per_sec:.2f}"])

    print(
        "\n"
        + tabulate(
            table_data,
            headers=["Operation", "Count", "Time (s)", "Ops/sec"],
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
            "similarity_search",
            "update_many",
            "get_all",
            "delete_many",
        ]
        summary_data = []
        for op in operations:
            row = [op]
            for size in dataset_sizes:
                matching = [r for r in mode_results[size] if r["operation"] == op]
                if matching:
                    ops_per_sec = matching[0].get(
                        "ops_per_sec", matching[0].get("searches_per_sec", 0)
                    )
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
                    "similarity_search",
                    "update_many",
                    "get_all",
                    "delete_many",
                ]
                for op in operations:
                    matching = [r for r in mode_results[size] if r["operation"] == op]
                    if matching:
                        ops_per_sec = matching[0].get(
                            "ops_per_sec", matching[0].get("searches_per_sec", 0)
                        )
                        time_val = matching[0].get(
                            "time", matching[0].get("avg_time", 0)
                        )
                        writer.writerow([op, f"{ops_per_sec:.2f}", f"{time_val:.4f}"])
                    else:
                        writer.writerow([op, "N/A", "N/A"])

            print(f"Exported {db_mode} ({size} records) to: {filename}")
