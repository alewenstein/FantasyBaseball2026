"""
Main script — fetch weekly results and write a summary.

Usage:
    python main.py <week_number>

Example:
    python main.py 5
"""

import sys
from fetch_results import fetch_week, print_results
from write_summary import write_summary


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <week_number>")
        print("Example: python main.py 1")
        sys.exit(1)

    week = int(sys.argv[1])

    results = fetch_week(week)
    print_results(results)

    print("Writing summary...\n")
    summary = write_summary(results)

    print("=== WEEKLY SUMMARY ===\n")
    print(summary)

    # Save to file so you can edit and send it
    output_file = f"summary_week_{week}.txt"
    with open(output_file, "w") as f:
        f.write(summary)
    print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    main()
