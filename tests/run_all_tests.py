#!/usr/bin/env python3
"""Standalone Test Runner for AI-Skills-Registry E2E Test Suite.

Executes all 4 test tiers, aggregates results, prints formatted diagnostic reports,
and exits with code 0 on complete pass or non-zero on failure.

Usage:
    python tests/run_all_tests.py
    python tests/run_all_tests.py --tier 1
    python tests/run_all_tests.py --tier 2,3
    python tests/run_all_tests.py --verbose
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pytest


TIER_DIRECTORIES = {
    "1": ("Tier 1: Category-Partition Feature Coverage", "tests/tier1_feature_coverage"),
    "2": ("Tier 2: Boundary Value Analysis & Corner Cases", "tests/tier2_boundary_corner"),
    "3": ("Tier 3: Pairwise Cross-Feature Integration", "tests/tier3_cross_feature"),
    "4": ("Tier 4: Real-World Workload Scenarios", "tests/tier4_real_world"),
}


class TierResultCollector:
    """Plugin to capture test outcome counts per tier run."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.total = 0

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.total += 1
            if report.passed:
                self.passed += 1
            elif report.failed:
                self.failed += 1
            elif report.skipped:
                self.skipped += 1


def run_tier(tier_key: str, tier_name: str, tier_path: str, verbose: bool = False) -> Dict[str, Any]:
    """Execute tests in a specific tier directory and return performance metrics."""
    collector = TierResultCollector()
    args = [tier_path, "-q"]
    if verbose:
        args.append("-v")

    start_time = time.perf_counter()
    exit_code = pytest.main(args, plugins=[collector])
    duration = time.perf_counter() - start_time

    return {
        "tier": tier_key,
        "name": tier_name,
        "path": tier_path,
        "exit_code": int(exit_code),
        "passed": collector.passed,
        "failed": collector.failed,
        "skipped": collector.skipped,
        "total": collector.total,
        "duration_sec": duration,
        "status": "PASS" if exit_code == 0 and collector.failed == 0 else "FAIL"
    }


def main():
    parser = argparse.ArgumentParser(description="AI-Skills-Registry E2E Test Suite Runner")
    parser.add_argument(
        "--tier",
        type=str,
        default="all",
        help="Tier(s) to execute: 1, 2, 3, 4, or 'all' (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose pytest reporting"
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    # Determine tiers to run
    if args.tier.lower() == "all":
        selected_tiers = ["1", "2", "3", "4"]
    else:
        selected_tiers = [t.strip() for t in args.tier.split(",") if t.strip() in TIER_DIRECTORIES]

    if not selected_tiers:
        print(f"Error: No valid tiers specified in '{args.tier}'. Valid tiers: 1, 2, 3, 4, all.")
        sys.exit(2)

    print("=" * 80)
    print("AI-SKILLS-REGISTRY COMPREHENSIVE E2E TEST RUNNER")
    print(f"Executing Tiers: {', '.join(selected_tiers)}")
    print(f"Working Directory: {project_root}")
    print("=" * 80)

    tier_results = []
    overall_exit = 0

    for t_key in selected_tiers:
        t_name, t_path = TIER_DIRECTORIES[t_key]
        print(f"\n>> Executing {t_name} ({t_path})...")
        res = run_tier(t_key, t_name, t_path, verbose=args.verbose)
        tier_results.append(res)
        if res["exit_code"] != 0:
            overall_exit = 1

    # Formatted Summary Table
    print("\n" + "=" * 80)
    print("TEST SUITE EXECUTION SUMMARY REPORT")
    print("=" * 80)
    print(f"{'Tier':<8} {'Passed':<8} {'Failed':<8} {'Total':<8} {'Duration':<10} {'Status':<8} {'Tier Description'}")
    print("-" * 80)

    total_passed = 0
    total_failed = 0
    total_count = 0
    total_duration = 0.0

    for r in tier_results:
        total_passed += r["passed"]
        total_failed += r["failed"]
        total_count += r["total"]
        total_duration += r["duration_sec"]
        status_color = r["status"]
        print(
            f"Tier {r['tier']:<3} {r['passed']:<8} {r['failed']:<8} {r['total']:<8} "
            f"{r['duration_sec']:.2f}s{'':<5} {status_color:<8} {r['name']}"
        )

    print("-" * 80)
    print(
        f"{'TOTAL':<8} {total_passed:<8} {total_failed:<8} {total_count:<8} "
        f"{total_duration:.2f}s{'':<5} {'PASS' if overall_exit == 0 else 'FAIL'}"
    )
    print("=" * 80)

    if overall_exit == 0:
        print("\nSUCCESS: All test tiers passed with 100% compliance!")
    else:
        print(f"\nFAILURE: One or more test tiers failed (exit code {overall_exit}).")

    sys.exit(overall_exit)


if __name__ == "__main__":
    main()
