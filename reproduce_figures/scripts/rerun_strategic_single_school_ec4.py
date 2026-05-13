#!/usr/bin/env python3
"""Rerun the Figure 10 EC.4 single-school strategic cache and replot it."""

from __future__ import annotations

import argparse
import os
import random
import site
import subprocess
import sys
from pathlib import Path


USER_SITE = site.getusersitepackages()
sys.path = [path for path in sys.path if path != USER_SITE]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
REPRO_ROOT = REPO_ROOT / "reproduce_figures"
DEFAULT_CACHE = REPO_ROOT / "simulation_data" / "cost_model_single_school_rerun"
DEFAULT_OUTPUT = REPO_ROOT / "second_round_MS" / "figures_ms_2025_revision"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--num-runs", type=int, default=10)
    parser.add_argument("--num-students", type=int, default=1000)
    parser.add_argument("--num-thresholds", type=int, default=250)
    parser.add_argument("--b1-var", type=float, default=2.0)
    parser.add_argument("--cost-a", type=float, default=0.5)
    parser.add_argument("--cost-b", type=float, default=3.0)
    parser.add_argument("--base-seed", type=int, default=20280812)
    parser.add_argument("--force-rerun", action="store_true")
    return parser.parse_args()


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    env.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")
    return env


def fmt_number(value: float | int) -> str:
    value = float(value)
    return str(int(value)) if value.is_integer() else f"{value:g}"


def import_pipeline():
    sys.path.insert(0, str(REPO_ROOT / "src"))
    import pipeline  # type: ignore

    return pipeline


def parameters(args: argparse.Namespace) -> dict:
    return {
        "SIMULATION_TYPE": "SINGLE_SCHOOL_COST_MODEL",
        "NUM_STUDENTS": args.num_students,
        "NUM_SCHOOL_TYPES": 1,
        "FRACTIONS_SCHOOL_TYPES": [1],
        "NUM_SCHOOLS": 1,
        "CAPACITY": 0.1,
        "NUM_FEATURES": 2,
        "NUM_GROUPS": 2,
        "FRACTIONS_GROUPS": [0.5, 0.5],
        "TRUESKILL_DIST": ("NORMAL", 0, 1),
        "FEATURE_DIST": ("NORMAL", 0, 1),
        "FEATURE_DIST_A0": ("NORMAL", 0, 1),
        "FEATURE_DIST_A1": ("NORMAL", 0, 1),
        "FEATURE_DIST_B0": ("NORMAL", 0, 1),
        "FEATURE_DIST_B1": ("NORMAL", 0, args.b1_var),
        "BINARY_SEARCH_NUM_THRESHOLDS": args.num_thresholds,
        "STUDENT_UTILITY": 5,
        "FEATURES_TO_USE": 0,
        "STUDENT_TEST_COST": {"A": args.cost_a, "B": args.cost_b},
    }


def instance_name(args: argparse.Namespace, run: int) -> str:
    return (
        f"A0_1_A1_1_B0_1_B1_{fmt_number(args.b1_var)}_"
        f"costA_{fmt_number(args.cost_a)}_costB_{fmt_number(args.cost_b)}_"
        f"N_{args.num_students}_run_{run}"
    )


def generate_cache(args: argparse.Namespace) -> None:
    pipeline = import_pipeline()
    params = parameters(args)
    for run in range(args.num_runs):
        instance_dir = args.cache_root / instance_name(args, run)
        if (instance_dir / "students_df.csv").exists() and not args.force_rerun:
            continue
        instance_dir.mkdir(parents=True, exist_ok=True)
        seed = args.base_seed + run
        random.seed(seed)
        np.random.seed(seed)
        students_df, schools_df, params_df = pipeline.pipeline(params)
        students_df.to_csv(instance_dir / "students_df.csv")
        schools_df.to_csv(instance_dir / "schools_df.csv")
        pd.Series(params_df).to_csv(instance_dir / "params_df.csv")


def replot(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        str(REPRO_ROOT / "scripts" / "replot_strategic_single_school_from_cache.py"),
        "--figure-set",
        "ec4_apply_by_skill",
        "--cache-root",
        str(args.cache_root),
        "--b1-var",
        fmt_number(args.b1_var),
        "--cost-a",
        fmt_number(args.cost_a),
        "--cost-b",
        fmt_number(args.cost_b),
        "--num-students",
        str(args.num_students),
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
