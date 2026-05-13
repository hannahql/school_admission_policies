#!/usr/bin/env python3
"""Heavy rerun for Figure 12 strategic cost-sweep panels.

This wrapper reconstructs the paper-facing single-school strategic cost sweep:
Group A has fixed test cost c_A, Group B's test cost varies, and the panels show
application probabilities, admitted academic merit, and diversity.
"""

from __future__ import annotations

import argparse
import os
import random
import site
import sys
from pathlib import Path


USER_SITE = site.getusersitepackages()
sys.path = [path for path in sys.path if path != USER_SITE]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = REPO_ROOT / "simulation_data" / "cost_model_single_school_cost_sweep"
DEFAULT_OUTPUT = REPO_ROOT / "plots_ms_revision" / "costA_0.5"
METRICS_FILE = "strategic_cost_sweep_metrics.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--num-runs", type=int, default=20)
    parser.add_argument("--num-students", type=int, default=10000)
    parser.add_argument("--num-thresholds", type=int, default=250)
    parser.add_argument("--cost-a", type=float, default=0.5)
    parser.add_argument("--min-cost-b", type=float, default=0.0)
    parser.add_argument("--max-cost-b", type=float, default=4.95)
    parser.add_argument("--cost-step", type=float, default=0.05)
    parser.add_argument("--b1-var", type=float, default=2.0)
    parser.add_argument("--base-seed", type=int, default=20280812)
    parser.add_argument("--no-rerun-missing", action="store_true")
    parser.add_argument("--force-rerun", action="store_true")
    return parser.parse_args()


def import_pipeline():
    sys.path.insert(0, str(REPO_ROOT / "src"))
    import pipeline  # type: ignore

    return pipeline


def cost_grid(args: argparse.Namespace) -> np.ndarray:
    return np.arange(args.min_cost_b, args.max_cost_b + 0.5 * args.cost_step, args.cost_step).round(2)


def base_parameters(args: argparse.Namespace, cost_b: float) -> dict:
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
        "STUDENT_TEST_COST": {"A": args.cost_a, "B": float(cost_b)},
    }


def school_metric(schools_df: pd.DataFrame, column: str) -> float:
    if column not in schools_df:
        raise ValueError(f"Missing {column} in schools_df")
    return float(schools_df[column].iloc[0])


def group_apply_rate(students_df: pd.DataFrame, group: str) -> float:
    if "take_test_at_threshold" not in students_df:
        raise ValueError("Missing take_test_at_threshold in students_df")
    return float(students_df.query("group == @group")["take_test_at_threshold"].mean())


def run_simulations(args: argparse.Namespace) -> pd.DataFrame:
    pipeline = import_pipeline()
    rows = []
    costs = cost_grid(args)
    for run in range(args.num_runs):
        for cost_index, cost_b in enumerate(costs):
            seed = args.base_seed + run * 1000 + cost_index
            random.seed(seed)
            np.random.seed(seed)
            students_df, schools_df, _ = pipeline.pipeline(base_parameters(args, float(cost_b)))
            rows.append(
                {
                    "cost_b": float(cost_b),
                    "run": run,
                    "p_apply_A": group_apply_rate(students_df, "A"),
                    "p_apply_B": group_apply_rate(students_df, "B"),
                    "avgadmittedskill_A": school_metric(schools_df, "avgadmittedskill_A"),
                    "avgadmittedskill_B": school_metric(schools_df, "avgadmittedskill_B"),
                    "avgadmittedskill": school_metric(schools_df, "avgadmittedskill"),
                    "frac_B": school_metric(schools_df, "frac_B"),
                }
            )

    df = pd.DataFrame(rows)
    args.cache_root.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.cache_root / METRICS_FILE, index=False)
    return df


def load_or_generate(args: argparse.Namespace) -> pd.DataFrame:
    metrics_path = args.cache_root / METRICS_FILE
    if metrics_path.exists() and not args.force_rerun:
        return pd.read_csv(metrics_path)
    if args.no_rerun_missing:
        raise FileNotFoundError(f"Missing {metrics_path}")
    return run_simulations(args)


def mean_and_ci(df: pd.DataFrame, column: str) -> pd.DataFrame:
    grouped = df.groupby("cost_b")[column]
    return pd.DataFrame(
        {
            "mean": grouped.mean(),
            "ci": 1.96 * grouped.sem(),
        }
    ).sort_index()


def plot_group_lines(
    df: pd.DataFrame,
    columns: tuple[str, str],
    labels: tuple[str, str],
    output_path: Path,
    ylabel: str,
    ylim: tuple[float, float] | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    colors = plt.cm.cubehelix(np.linspace(0.15, 0.75, 2))
    for color, column, label in zip(colors, columns, labels):
        stats = mean_and_ci(df, column)
        x = stats.index.astype(float).to_numpy()
        y = stats["mean"].to_numpy(dtype=float)
        e = stats["ci"].fillna(0).to_numpy(dtype=float)
        ax.plot(x, y, linewidth=2, color=color, label=label)
        ax.fill_between(x, y - e, y + e, color=color, alpha=0.2)
    ax.set_xlabel(r"Cost for Group B, $c_B$", fontsize=15)
    ax.set_ylabel(ylabel, fontsize=15)
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.legend(frameon=False, fontsize=13)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(output_path)


def plot_single_line(df: pd.DataFrame, column: str, output_path: Path, ylabel: str, ylim: tuple[float, float] | None = None) -> None:
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    stats = mean_and_ci(df, column)
    x = stats.index.astype(float).to_numpy()
    y = stats["mean"].to_numpy(dtype=float)
    e = stats["ci"].fillna(0).to_numpy(dtype=float)
    color = plt.cm.cubehelix(0.35)
    ax.plot(x, y, linewidth=2, color=color)
    ax.fill_between(x, y - e, y + e, color=color, alpha=0.2)
    ax.set_xlabel(r"Cost for Group B, $c_B$", fontsize=15)
    ax.set_ylabel(ylabel, fontsize=15)
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(output_path)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    df = load_or_generate(args)

    plot_group_lines(
        df,
        ("p_apply_A", "p_apply_B"),
        ("Group A", "Group B"),
        args.output_dir / "p_apply.png",
        "Probability of applying",
        ylim=(0, 1),
    )
    plot_group_lines(
        df,
        ("avgadmittedskill_A", "avgadmittedskill_B"),
        ("Group A", "Group B"),
        args.output_dir / "avg_admitted_skill.png",
        "Average admitted skill",
    )
    plot_single_line(
        df,
        "frac_B",
        args.output_dir / "frac_B_cost.png",
        r"Diversity level, $\tau$",
        ylim=(0, 1),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
