#!/usr/bin/env python3
"""Heavy rerun for Figure 11 strategic single-school panels.

This is an additive wrapper around the existing cost-model pipeline. It writes
compact per-run school-level cache files, then replots the three EC.5 panels
used by the ordered arXiv reproduction bundle.
"""

from __future__ import annotations

import argparse
import ast
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
DEFAULT_CACHE = REPO_ROOT / "simulation_data" / "cost_model_single_school_fix_A1_equal_B1"
DEFAULT_OUTPUT = REPO_ROOT / "second_round_MS" / "figures_ms_2025_revision"
DICT_COLUMNS = {
    "admitted_students",
    "prob_apply_rawskill_A",
    "prob_apply_rawskill_B",
    "prob_apply_rawtest_A",
    "prob_apply_rawtest_B",
    "prob_apply_test_A",
    "prob_apply_test_B",
    "prob_apply_skill_A",
    "prob_apply_skill_B",
    "avgadmittedskill",
    "IF",
    "IF_rawskill",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--num-runs", type=int, default=50)
    parser.add_argument("--num-students", type=int, default=5000)
    parser.add_argument("--num-thresholds", type=int, default=300)
    parser.add_argument("--cost-a", type=float, default=0.5)
    parser.add_argument("--max-cost-b", type=float, default=4.75)
    parser.add_argument("--cost-step", type=float, default=0.25)
    parser.add_argument("--b1-vars", default="1,4")
    parser.add_argument("--base-seed", type=int, default=20280812)
    parser.add_argument("--no-rerun-missing", action="store_true")
    parser.add_argument("--force-rerun", action="store_true")
    parser.add_argument("--save-students", action="store_true")
    return parser.parse_args()


def fmt_number(value: float | int) -> str:
    value = float(value)
    return str(int(value)) if value.is_integer() else f"{value:g}"


def parse_float_list(text: str) -> list[float]:
    return [float(part.strip()) for part in text.split(",") if part.strip()]


def literal_converter(value):
    if not isinstance(value, str):
        return value
    text = value.strip()
    if text.startswith("defaultdict"):
        try:
            text = text[text.index("{") : text.rindex("}") + 1]
        except ValueError:
            return value
    try:
        return ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return value


def read_schools_df(path: Path) -> pd.DataFrame:
    converters = {column: literal_converter for column in DICT_COLUMNS}
    return pd.read_csv(path, index_col=0, converters=converters)


def import_pipeline():
    sys.path.insert(0, str(REPO_ROOT / "src"))
    import pipeline  # type: ignore

    return pipeline


def build_base_parameters(args: argparse.Namespace, b1_var: float) -> dict:
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
        "FEATURE_DIST_B1": ("NORMAL", 0, b1_var),
        "BINARY_SEARCH_NUM_THRESHOLDS": args.num_thresholds,
        "STUDENT_UTILITY": 5,
        "FEATURES_TO_USE": 0,
    }


def instance_name(b1_var: float, run: int, args: argparse.Namespace) -> str:
    return f"A0_1_A1_1_B0_1_B1_{fmt_number(b1_var)}_N_{args.num_students}_run_{run}"


def cost_key(cost_a: float, cost_b: float) -> tuple[float, float]:
    return (float(cost_a), float(cost_b))


def schools_file(instance_dir: Path, cost: tuple[float, float]) -> Path:
    return instance_dir / f"schools_df_cost_{cost}.csv"


def ensure_school_cache(
    pipeline,
    args: argparse.Namespace,
    instance_dir: Path,
    parameters: dict,
    cost: tuple[float, float],
    seed: int,
) -> None:
    output_file = schools_file(instance_dir, cost)
    if output_file.exists() and not args.force_rerun:
        return
    if args.no_rerun_missing:
        raise FileNotFoundError(f"Missing {output_file}")

    instance_dir.mkdir(parents=True, exist_ok=True)
    run_parameters = parameters.copy()
    run_parameters["STUDENT_TEST_COST"] = {"A": cost[0], "B": cost[1]}
    random.seed(seed)
    np.random.seed(seed)
    students_df, schools_df, params_df = pipeline.pipeline(run_parameters)
    schools_df.to_csv(output_file)
    pd.Series(params_df).to_csv(instance_dir / f"params_df_cost_{cost}.csv")
    if args.save_students:
        students_df.to_csv(instance_dir / f"students_df_cost_{cost}.csv")


def load_or_generate(args: argparse.Namespace) -> dict[tuple[float, int, float], pd.DataFrame]:
    pipeline = import_pipeline()
    b1_vars = parse_float_list(args.b1_vars)
    cost_bs = np.arange(0, args.max_cost_b + 0.5 * args.cost_step, args.cost_step).round(2)
    records: dict[tuple[float, int, float], pd.DataFrame] = {}

    for b1_index, b1_var in enumerate(b1_vars):
        base_parameters = build_base_parameters(args, b1_var)
        for run in range(args.num_runs):
            name = instance_name(b1_var, run, args)
            instance_dir = args.cache_root / name
            for cost_index, cost_b in enumerate(cost_bs):
                cost = cost_key(args.cost_a, float(cost_b))
                seed = args.base_seed + b1_index * 100000 + run * 1000 + cost_index
                ensure_school_cache(pipeline, args, instance_dir, base_parameters, cost, seed)
                records[(b1_var, run, float(cost_b))] = read_schools_df(schools_file(instance_dir, cost))

    return records


def school_value(schools_df: pd.DataFrame, column: str):
    if column not in schools_df:
        raise ValueError(f"Missing {column} in generated schools_df")
    return schools_df[column].iloc[0]


def metric_frame(records: dict[tuple[float, int, float], pd.DataFrame], b1_var: float, metric: str) -> pd.DataFrame:
    runs = sorted({run for b1, run, _ in records if b1 == b1_var})
    data = {}
    for run in runs:
        series = {
            cost_b: float(school_value(schools_df, metric))
            for (b1, run_id, cost_b), schools_df in records.items()
            if b1 == b1_var and run_id == run
        }
        data[run] = pd.Series(series).sort_index()
    return pd.DataFrame(data).sort_index()


def plot_metric(
    records: dict[tuple[float, int, float], pd.DataFrame],
    b1_vars: list[float],
    metric: str,
    output_path: Path,
    ylabel: str,
    cost_a: float,
) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    colors = plt.cm.cubehelix(np.linspace(0.15, 0.75, len(b1_vars)))
    for color, b1_var in zip(colors, b1_vars):
        frame = metric_frame(records, b1_var, metric)
        if metric == "frac_A":
            frame = 1 - frame
        mean = frame.mean(axis=1)
        err = 1.96 * frame.sem(axis=1)
        x = mean.index.astype(float).to_numpy()
        y = mean.to_numpy(dtype=float)
        e = err.fillna(0).to_numpy(dtype=float)
        ax.plot(x, y, linewidth=2, color=color, label=rf"$\sigma_K^2={fmt_number(b1_var)}$")
        ax.fill_between(x, y - e, y + e, color=color, alpha=0.2)

    ax.axvline(cost_a, color="grey", linestyle="--")
    ax.set_xlabel("Cost for group B", fontsize=20)
    ax.set_ylabel(ylabel, fontsize=20)
    ax.tick_params(axis="both", labelsize=15)
    ax.legend(frameon=False, fontsize=15, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(output_path)


def dict_to_series(value) -> pd.Series:
    if isinstance(value, str):
        value = literal_converter(value)
    if not isinstance(value, dict):
        raise ValueError("Expected probability-by-skill dictionary")
    return pd.Series({float(key): float(val) for key, val in value.items()}).sort_index()


def plot_if(
    records: dict[tuple[float, int, float], pd.DataFrame],
    b1_vars: list[float],
    output_path: Path,
    target_cost_b: float = 3.0,
) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    colors = plt.cm.cubehelix(np.linspace(0.15, 0.75, len(b1_vars)))
    for color, b1_var in zip(colors, b1_vars):
        runs = sorted({run for b1, run, cost_b in records if b1 == b1_var and abs(cost_b - target_cost_b) < 1e-9})
        series_by_run = {}
        for run in runs:
            schools_df = records[(b1_var, run, target_cost_b)]
            series_by_run[run] = (
                dict_to_series(school_value(schools_df, "prob_apply_skill_A"))
                - dict_to_series(school_value(schools_df, "prob_apply_skill_B"))
            ).sort_index().rolling(10).mean()
        frame = pd.DataFrame(series_by_run).sort_index()
        mean = frame.mean(axis=1)
        err = 1.96 * frame.sem(axis=1)
        x = mean.index.astype(float).to_numpy()
        y = mean.to_numpy(dtype=float)
        e = err.fillna(0).to_numpy(dtype=float)
        ax.plot(x, y, linewidth=2, color=color, label=rf"$\sigma_K^2={fmt_number(b1_var)}$")
        ax.fill_between(x, y - e, y + e, color=color, alpha=0.2)

    ax.axhline(0, color="grey", linewidth=1)
    ax.set_xlabel(r"True skill, $q$", fontsize=20)
    ax.set_ylabel("Individual Fairness Gap", fontsize=20)
    ax.tick_params(axis="both", labelsize=15)
    ax.legend(frameon=False, fontsize=15)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(output_path)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = load_or_generate(args)
    b1_vars = parse_float_list(args.b1_vars)
    plot_metric(
        records,
        b1_vars,
        "avgadmittedskill",
        args.output_dir / "avgadmittedskill_strategic.png",
        "Average admitted skill",
        args.cost_a,
    )
    plot_metric(
        records,
        b1_vars,
        "frac_A",
        args.output_dir / "frac_A_strategic.png",
        r"Diversity level, $\tau$",
        args.cost_a,
    )
    plot_if(records, b1_vars, args.output_dir / "IF_strategic.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
