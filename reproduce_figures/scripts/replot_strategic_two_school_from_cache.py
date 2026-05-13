#!/usr/bin/env python3
"""Replot strategic two-school heatmaps from saved simulation cache."""

from __future__ import annotations

import argparse
import json
import os
import site
import sys
import time
from pathlib import Path


USER_SITE = site.getusersitepackages()
sys.path = [path for path in sys.path if path != USER_SITE]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")

import matplotlib

matplotlib.use("Agg")
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = REPO_ROOT / "simulation_data" / "20260323"
DEFAULT_OUTPUT = REPO_ROOT / "second_round_MS" / "figures_ms_2025_dec_revision"
POLICIES = ["FULL_FULL_test", "FULL_SUB_test", "SUB_FULL_test", "SUB_SUB_test"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--utility-a", type=float, default=3)
    parser.add_argument("--utility-b", type=float, default=2)
    parser.add_argument("--cost", type=float, action="append", default=[0.5, 1.5, 2.0])
    parser.add_argument("--read-retries", type=int, default=5)
    parser.add_argument("--read-retry-sleep", type=float, default=1.0)
    return parser.parse_args()


def policy_to_name(policy: str) -> str:
    return policy.replace("_test", "")


def read_json_with_retries(path: Path, attempts: int, sleep_seconds: float):
    last_error = None
    for attempt in range(max(1, attempts)):
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except OSError as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(sleep_seconds)
    raise last_error


def read_csv_with_retries(path: Path, attempts: int, sleep_seconds: float) -> pd.DataFrame:
    last_error = None
    for attempt in range(max(1, attempts)):
        try:
            return pd.read_csv(path)
        except OSError as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(sleep_seconds)
    raise last_error


def read_one(policy_dir: Path, index: str, attempts: int, sleep_seconds: float) -> dict[str, object]:
    params = read_json_with_retries(policy_dir / f"parameters_of_interest_{index}.json", attempts, sleep_seconds)
    schools = read_csv_with_retries(policy_dir / f"schools_df_{index}.csv", attempts, sleep_seconds)
    school_column = "school" if "school" in schools.columns else "school_type"
    row = {
        "Policy": policy_to_name(policy_dir.name),
        "Index": int(index),
        "CAPACITY_a": params["CAPACITY_a"],
        "CAPACITY_b": params["CAPACITY_b"],
        "UTILITY_a": params["STUDENT_UTILITY"]["a"],
        "UTILITY_b": params["STUDENT_UTILITY"]["b"],
        "STUDENT_TEST_COST": params["STUDENT_TEST_COST"],
        "avgadmittedskill_school_a": schools.loc[schools[school_column] == "a", "avgadmittedskill"].iloc[0],
        "avgadmittedskill_school_b": schools.loc[schools[school_column] == "b", "avgadmittedskill"].iloc[0],
    }
    return row


def read_cache(cache_root: Path, attempts: int, sleep_seconds: float) -> pd.DataFrame:
    records = []
    for policy in POLICIES:
        policy_dir = cache_root / policy
        if not policy_dir.is_dir():
            raise FileNotFoundError(f"Missing policy cache directory: {policy_dir}")
        for params_path in policy_dir.glob("parameters_of_interest_*.json"):
            index = params_path.stem.rsplit("_", 1)[-1]
            records.append(read_one(policy_dir, index, attempts, sleep_seconds))
    if not records:
        raise ValueError(f"No cached two-school results found in {cache_root}")
    return pd.DataFrame(records)


def main() -> int:
    args = parse_args()
    sys.path.insert(0, str(REPO_ROOT))
    from visualization.two_school_strategic_plots import plot_avg_admitted_skill_by_policy_heatmap

    results = read_cache(args.cache_root, args.read_retries, args.read_retry_sleep)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for cost in args.cost:
        plot_avg_admitted_skill_by_policy_heatmap(
            results_df=results,
            feature_to_vary=None,
            target_values={
                "STUDENT_TEST_COST": cost,
                "UTILITY_a": args.utility_a,
                "UTILITY_b": args.utility_b,
            },
            fig_directory=str(args.output_dir),
            plot_standard_errors=True,
        )
        print(args.output_dir / f"avg_skill_heatmap_STUDENT_TEST_COST={cost:g}_UTILITY_a={args.utility_a:g}_UTILITY_b={args.utility_b:g}_sems.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
