#!/usr/bin/env python3
"""Rerun the two-school strategic simulation cache for Figures 6 and 14."""

from __future__ import annotations

import argparse
import itertools
import os
import site
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path


USER_SITE = site.getusersitepackages()
sys.path = [path for path in sys.path if path != USER_SITE]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")


REPO_ROOT = Path(__file__).resolve().parents[2]
REPRO_ROOT = REPO_ROOT / "reproduce_figures"
DEFAULT_CACHE = REPO_ROOT / "simulation_data" / "20260323_rerun"
DEFAULT_OUTPUT = REPO_ROOT / "second_round_MS" / "figures_ms_2025_dec_revision"
POLICY_NAMES = {
    (-1, -1): "SUB_SUB",
    (-1, 0): "SUB_FULL",
    (0, -1): "FULL_SUB",
    (0, 0): "FULL_FULL",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--n-runs", type=int, default=5)
    parser.add_argument("--n-processes", type=int, default=1)
    parser.add_argument("--utility-a", type=float, default=3)
    parser.add_argument("--utility-b", type=float, default=2)
    parser.add_argument("--test-costs", default="0.5,1.5,2")
    parser.add_argument("--force-rerun", action="store_true")
    return parser.parse_args()


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    env.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")
    return env


def parse_float_list(text: str) -> list[float]:
    return [float(part.strip()) for part in text.split(",") if part.strip()]


def build_args(args: argparse.Namespace) -> list[tuple]:
    valid_combinations = [
        (0.2, 0.2, args.utility_a, args.utility_b, cost)
        for cost in parse_float_list(args.test_costs)
        if args.utility_a > args.utility_b
    ]
    run_args = []
    for features_to_use_a, features_to_use_b in POLICY_NAMES:
        policy_name = POLICY_NAMES[(features_to_use_a, features_to_use_b)]
        (args.cache_root / f"{policy_name}_test").mkdir(parents=True, exist_ok=True)

    for base_idx, (cap_a, cap_b, util_a, util_b, test_cost) in enumerate(valid_combinations):
        for run_num in range(args.n_runs):
            idx = base_idx + run_num * 100
            for features_to_use_a, features_to_use_b in itertools.product([-1, 0], repeat=2):
                policy_name = POLICY_NAMES[(features_to_use_a, features_to_use_b)]
                output_directory = str(args.cache_root / f"{policy_name}_test")
                run_args.append(
                    (
                        idx,
                        cap_a,
                        cap_b,
                        util_a,
                        util_b,
                        test_cost,
                        features_to_use_a,
                        features_to_use_b,
                        output_directory,
                    )
                )
    return run_args


def cache_exists(args: argparse.Namespace) -> bool:
    return all((args.cache_root / f"{policy}_test" / "parameters_of_interest_0.json").exists() for policy in POLICY_NAMES.values())


def generate_cache(args: argparse.Namespace) -> None:
    if cache_exists(args) and not args.force_rerun:
        return
    sys.path.insert(0, str(REPO_ROOT))
    from run_two_school_cost_model import run_simulation  # type: ignore

    run_args = build_args(args)
    if args.n_processes == 1:
        for run_arg in run_args:
            run_simulation(run_arg)
    else:
        with Pool(args.n_processes) as pool:
            pool.map(run_simulation, run_args)


def replot(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        str(REPRO_ROOT / "scripts" / "replot_strategic_two_school_from_cache.py"),
        "--cache-root",
        str(args.cache_root),
        "--utility-a",
        str(args.utility_a),
        "--utility-b",
        str(args.utility_b),
        "--output-dir",
        str(args.output_dir),
    ]
    subprocess.run(command, cwd=REPO_ROOT, env=command_env(), check=True)


def main() -> int:
    args = parse_args()
    generate_cache(args)
    replot(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
