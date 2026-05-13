#!/usr/bin/env python3
"""Replot strategic single-school figures from saved simulation cache."""

from __future__ import annotations

import argparse
import os
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
DEFAULT_CACHE = REPO_ROOT / "simulation_data" / "cost_model_single_school"
DEFAULT_OUTPUT = REPO_ROOT / "second_round_MS" / "figures_ms_2025_revision"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure-set", choices=["ec4_apply_by_skill"], default="ec4_apply_by_skill")
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--b1-var", type=str, default="2")
    parser.add_argument("--cost-a", type=str, default="0.5")
    parser.add_argument("--cost-b", type=str, default="3")
    parser.add_argument("--num-students", type=str, default="1000")
    return parser.parse_args()


def selected_run_dirs(args: argparse.Namespace) -> list[Path]:
    needle = f"B1_{args.b1_var}_costA_{args.cost_a}_costB_{args.cost_b}_N_{args.num_students}_run_"
    dirs = [path for path in args.cache_root.iterdir() if path.is_dir() and needle in path.name]
    if not dirs:
        raise FileNotFoundError(f"No EC.4 cache directories found in {args.cache_root} matching {needle}")
    return sorted(dirs)


def load_group_apply_by_skill(run_dir: Path) -> dict[str, pd.Series]:
    students = pd.read_csv(run_dir / "students_df.csv")
    if "take_test_at_threshold" not in students:
        raise ValueError(f"Missing take_test_at_threshold column in {run_dir / 'students_df.csv'}")
    students["take_test_at_threshold"] = students["take_test_at_threshold"].map(lambda value: str(value).lower() == "true")

    roundmult = 5
    students["skillcut_coarse"] = (students["skill"].rank(pct=True) * roundmult).round(1) / roundmult
    skill_col = "skillcut_coarse"

    result = {}
    for group in ["A", "B"]:
        group_df = students.query("group == @group")
        result[group] = group_df.groupby(skill_col)["take_test_at_threshold"].mean().sort_index()
    return result


def plot_ec4_apply_by_skill(args: argparse.Namespace) -> Path:
    run_dirs = selected_run_dirs(args)
    by_group: dict[str, list[pd.Series]] = {"A": [], "B": []}
    for run_dir in run_dirs:
        run_result = load_group_apply_by_skill(run_dir)
        for group in ["A", "B"]:
            by_group[group].append(run_result[group])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "p_apply_by_skill_group.png"

    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    colors = plt.cm.cubehelix(np.linspace(0.15, 0.75, 2))
    for color, group in zip(colors, ["A", "B"]):
        data = pd.concat(by_group[group], axis=1).sort_index()
        mean = data.mean(axis=1)
        stderr = 2 * data.std(axis=1) / np.sqrt(data.shape[1])
        ax.plot(mean.index.astype(float), mean.values, label=f"Group {group}", linewidth=2, color=color)
        ax.fill_between(mean.index.astype(float), mean - stderr, mean + stderr, alpha=0.2, color=color)

    ax.legend(frameon=False, fontsize=15)
    ax.set_xlabel(r"True skill, $q$", fontsize=20)
    ax.set_ylabel(r"P(apply | q)", fontsize=20)
    ax.tick_params(axis="both", labelsize=15)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(output_path)
    return output_path


def main() -> int:
    args = parse_args()
    if args.figure_set == "ec4_apply_by_skill":
        plot_ec4_apply_by_skill(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
