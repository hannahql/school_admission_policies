#!/usr/bin/env python3
"""Heavy rerun for Figure 13 strategic drop-test heatmaps.

This wrapper reconstructs the paper-facing Figure 13 inputs from simulations:
for each Group B test variance and Group B test cost, it compares the strategic
cost-model outcome to a no-test/drop-test baseline, then plots the change in
diversity and academic merit after dropping the test.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
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
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = REPO_ROOT / "simulation_data" / "cost_model_single_school_drop_test_heatmaps"
DEFAULT_OUTPUT = REPO_ROOT / "plots_ms_revision" / "costA_0.5_old"
METRICS_FILE = "drop_test_heatmap_metrics.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--num-runs", type=int, default=20)
    parser.add_argument("--num-students", type=int, default=10000)
    parser.add_argument("--num-thresholds", type=int, default=250)
    parser.add_argument("--cost-a", type=float, default=0.5)
    parser.add_argument("--min-cost-b", type=float, default=0.5)
    parser.add_argument("--max-cost-b", type=float, default=4.75)
    parser.add_argument("--cost-step", type=float, default=0.25)
    parser.add_argument("--b1-vars", default="1,2,3,4")
    parser.add_argument("--base-seed", type=int, default=20280812)
    parser.add_argument("--workers", type=int, default=1, help="Parallel worker processes over B-variance/run jobs.")
    parser.add_argument("--no-rerun-missing", action="store_true")
    parser.add_argument("--force-rerun", action="store_true")
    return parser.parse_args()


def parse_float_list(text: str) -> list[float]:
    return [float(part.strip()) for part in text.split(",") if part.strip()]


def fmt_number(value: float | int) -> str:
    value = float(value)
    return str(int(value)) if value.is_integer() else f"{value:g}"


def import_pipeline():
    sys.path.insert(0, str(REPO_ROOT / "src"))
    import pipeline  # type: ignore

    return pipeline


def base_parameters(args: argparse.Namespace, b1_var: float, cost_b: float | None = None) -> dict:
    params = {
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
        "FEATURE_DIST_B1": ("NORMAL", 0, b1_var),
        "BINARY_SEARCH_NUM_THRESHOLDS": args.num_thresholds,
        "STUDENT_UTILITY": 5,
        "FEATURES_TO_USE": 0,
    }
    if cost_b is not None:
        params["STUDENT_TEST_COST"] = {"A": args.cost_a, "B": float(cost_b)}
    return params


def drop_test_parameters(args: argparse.Namespace, b1_var: float) -> dict:
    params = base_parameters(args, b1_var)
    params["SIMULATION_TYPE"] = "SINGLE_SCHOOL"
    params["FEATURES_TO_USE_a"] = -1
    return params


def school_metric(schools_df: pd.DataFrame, column: str, default: float = 0.0) -> float:
    if column not in schools_df:
        return default
    return float(schools_df[column].iloc[0])


def cost_grid(args: argparse.Namespace) -> np.ndarray:
    return np.arange(args.min_cost_b, args.max_cost_b + 0.5 * args.cost_step, args.cost_step).round(2)


def run_drop_test_task(task: tuple[argparse.Namespace, int, float, int, list[float]]) -> list[dict[str, float | int]]:
    args, b1_index, b1_var, run, costs = task
    pipeline = import_pipeline()
    rows: list[dict[str, float | int]] = []
    drop_seed = args.base_seed + b1_index * 100000 + run * 1000
    random.seed(drop_seed)
    np.random.seed(drop_seed)
    _, drop_schools_df, _ = pipeline.pipeline(drop_test_parameters(args, b1_var))
    drop_frac_b = school_metric(drop_schools_df, "frac_B")
    drop_avg_skill = school_metric(drop_schools_df, "avgadmittedskill")

    for cost_index, cost_b in enumerate(costs):
        seed = drop_seed + cost_index + 1
        random.seed(seed)
        np.random.seed(seed)
        _, schools_df, _ = pipeline.pipeline(base_parameters(args, b1_var, float(cost_b)))
        rows.append(
            {
                "b1_var": float(b1_var),
                "cost_b": float(cost_b),
                "run": run,
                "frac_B": school_metric(schools_df, "frac_B"),
                "avgadmittedskill": school_metric(schools_df, "avgadmittedskill"),
                "drop_frac_B": drop_frac_b,
                "drop_avgadmittedskill": drop_avg_skill,
            }
        )
    return rows


def run_simulations(args: argparse.Namespace) -> pd.DataFrame:
    b1_vars = parse_float_list(args.b1_vars)
    costs = [float(cost_b) for cost_b in cost_grid(args)]
    tasks = [(args, b1_index, b1_var, run, costs) for b1_index, b1_var in enumerate(b1_vars) for run in range(args.num_runs)]
    workers = max(1, int(args.workers))
    if workers == 1:
        nested_rows = [run_drop_test_task(task) for task in tasks]
    else:
        nested_rows = []
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(run_drop_test_task, task) for task in tasks]
            for future in as_completed(futures):
                nested_rows.append(future.result())

    rows = [row for task_rows in nested_rows for row in task_rows]
    df = pd.DataFrame(rows).sort_values(["b1_var", "run", "cost_b"]).reset_index(drop=True)
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


def plot_heatmap(df: pd.DataFrame, value_column: str, output_path: Path, title: str, cbar_label: str) -> None:
    grouped = df.groupby(["cost_b", "b1_var"], as_index=False)[value_column].mean()
    pivot = grouped.pivot(index="cost_b", columns="b1_var", values=value_column).sort_index().sort_index(axis=1)
    display = pivot.iloc[::-1]
    values = display.to_numpy(dtype=float)
    finite = values[np.isfinite(values)]
    limit = max(abs(float(finite.min())), abs(float(finite.max()))) if finite.size else 1.0
    if limit == 0:
        limit = 1.0

    fig, ax = plt.subplots(figsize=(6, 4.6))
    im = ax.imshow(values, aspect="auto", cmap="coolwarm", norm=TwoSlopeNorm(vcenter=0, vmin=-limit, vmax=limit))
    ax.set_xticks(np.arange(len(display.columns)))
    ax.set_xticklabels([fmt_number(value) for value in display.columns], rotation=45, ha="right")
    y_step = max(1, len(display.index) // 8)
    yticks = np.arange(0, len(display.index), y_step)
    ax.set_yticks(yticks)
    ax.set_yticklabels([fmt_number(display.index[i]) for i in yticks])
    ax.set_xlabel(r"Variance of Group B test score, $\sigma^2_{BK}$", fontsize=13)
    ax.set_ylabel(r"Cost for Group B, $c_B$", fontsize=13)
    ax.set_title(title, fontsize=13)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(output_path)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    df = load_or_generate(args)
    df = df.copy()
    df["drop_test_diversity_change"] = df["drop_frac_B"] - df["frac_B"]
    df["drop_test_academic_merit_change"] = df["drop_avgadmittedskill"] - df["avgadmittedskill"]

    plot_heatmap(
        df,
        "drop_test_diversity_change",
        args.output_dir / "drop_test_diversity_level_vary_costB_varB_heatmap.png",
        "Change in diversity after dropping test",
        "No-test diversity minus strategic diversity",
    )
    plot_heatmap(
        df,
        "drop_test_academic_merit_change",
        args.output_dir / "drop_test_academic_merit_vary_costB_varB_heatmap.png",
        "Change in academic merit after dropping test",
        "No-test merit minus strategic merit",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
