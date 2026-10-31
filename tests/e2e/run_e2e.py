#!/usr/bin/env python3
"""E2E Test Runner for Stock Trend Prediction & Quantitative Platform.

Usage:
    python tests/e2e/run_e2e.py                     # Run all tiers (Tiers 1-4)
    python tests/e2e/run_e2e.py --tier 1            # Run Tier 1 only
    python tests/e2e/run_e2e.py --tier 2            # Run Tier 2 only
    python tests/e2e/run_e2e.py --tier 3            # Run Tier 3 only
    python tests/e2e/run_e2e.py --tier 4            # Run Tier 4 only
    python tests/e2e/run_e2e.py --target http://localhost:8000 # Target live server
    python tests/e2e/run_e2e.py --force-mock        # Force contract reference engine
"""

import argparse
import os
import sys
import time
from pathlib import Path
import pytest
import httpx


TIER_FILES = {
    1: "test_tier1_feature_coverage.py",
    2: "test_tier2_boundary_corner_cases.py",
    3: "test_tier3_cross_feature_isolation.py",
    4: "test_tier4_real_world_workload.py",
}

TIER_NAMES = {
    1: "Tier 1: Feature Coverage (>=5 tests per feature)",
    2: "Tier 2: Boundary & Corner Cases (BVA, Malicious, Schema Errors)",
    3: "Tier 3: Cross-Feature Combinations & Multi-Tenant Isolation (Pairwise)",
    4: "Tier 4: Real-World Scenarios & Market Microstructure Audits",
}


def check_live_server(url: str) -> bool:
    """Check if the target server is alive and responding."""
    try:
        with httpx.Client(timeout=2.0) as client:
            res = client.get(f"{url.rstrip('/')}/health")
            return res.status_code == 200
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Opaque-box E2E Test Suite Runner for VN Stock Production Upgrade",
    )
    parser.add_argument(
        "--tier",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run only the specified test tier (1, 2, 3, or 4)",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=os.environ.get("E2E_BASE_URL", ""),
        help="Base URL of live backend (e.g., http://localhost:8000)",
    )
    parser.add_argument(
        "--force-mock",
        action="store_true",
        help="Force in-process contract reference mode even if live server is reachable",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose test output",
    )
    parser.add_argument(
        "-k", "--keyword",
        type=str,
        help="Filter tests by keyword expression",
    )

    args = parser.parse_args()

    # Determine execution target
    target_url = args.target.rstrip("/") if args.target else ""
    force_mock = args.force_mock or os.environ.get("E2E_FORCE_MOCK", "").lower() in ("1", "true")

    is_live = False
    if not force_mock and target_url:
        is_live = check_live_server(target_url)
    elif not force_mock and not target_url:
        # Check default localhost:8000
        if check_live_server("http://localhost:8000"):
            target_url = "http://localhost:8000"
            is_live = True

    if is_live:
        os.environ["E2E_BASE_URL"] = target_url
        mode_label = f"LIVE TARGET ({target_url})"
    else:
        os.environ["E2E_FORCE_MOCK"] = "1"
        mode_label = "IN-PROCESS CONTRACT REFERENCE (Progressive Testability)"

    e2e_dir = Path(__file__).resolve().parent

    print("\n" + "=" * 78)
    print("  VN STOCK PREDICTION PLATFORM — E2E TEST RUNNER")
    print(f"  Mode: {mode_label}")
    print(f"  Root: {e2e_dir}")
    print("=" * 78 + "\n")

    selected_tiers = [args.tier] if args.tier else [1, 2, 3, 4]

    pytest_args = [
        "-q" if not args.verbose else "-v",
        "--tb=short",
        "-W", "ignore::DeprecationWarning",
    ]

    for t in selected_tiers:
        test_file = e2e_dir / TIER_FILES[t]
        pytest_args.append(str(test_file))

    if args.keyword:
        pytest_args.extend(["-k", args.keyword])

    start_time = time.time()
    exit_code = pytest.main(pytest_args)
    duration = time.time() - start_time

    print("\n" + "-" * 78)
    print(f"  E2E Test Execution Summary:")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Execution Mode: {mode_label}")
    if exit_code == 0:
        print("  Status: ALL TIERS PASSED [100% SUCCESS]")
    else:
        print(f"  Status: FAILED with exit code {exit_code}")
    print("-" * 78 + "\n")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
