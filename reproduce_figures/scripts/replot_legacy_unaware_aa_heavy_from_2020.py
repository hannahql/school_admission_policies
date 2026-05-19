#!/usr/bin/env python3
"""Heavy rerun for Figure 15 Pareto panel plus cached IF panel.

The migrated paperclean5 cache contains the individual-fairness inputs but not
the Pareto metrics. This wrapper regenerates only the missing Pareto metric
table from the traced 2020 parameter grid and then calls the legacy plotting
helper. It also invokes the existing cache-based IF wrapper so Figure 15 has a
single generator entry in the ordered reproduction runner.
"""

from __future__ import annotations

import argparse
import copy
import os
import random
import site
import subprocess
import sys
from pathlib import Path


USER_SITE = site.getusersitepackages()
sys.path = [path for path in sys.path if path != USER_SITE]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pandas as pd

from legacy_overlay import configure_overlay, import_legacy_file


REPO_ROOT = Path(__file__).resolve().parents[2]
REPRO_ROOT = REPO_ROOT / "reproduce_figures"
DEFAULT_LEGACY_CODE_DIR = REPO_ROOT / "reproduce_figures" / "legacy_code" / "2020_sims"
DEFAULT_CACHE = REPO_ROOT / "reproduce_figures" / "inputs"
DEFAULT_IF_CACHE = REPO_ROOT / "reproduce_figures" / "inputs"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "reproduce_figures" / "workspace" / "generated" / "plots"
LEGACY_PLOTS_DIR_ENV = "MS_FIGURES_LEGACY_PLOTS_DIR"
LABEL = "paper_simulationsbudget_pareto_update2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-code-dir", type=Path, default=DEFAULT_LEGACY_CODE_DIR)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--if-cache-dir", type=Path, default=DEFAULT_IF_CACHE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--repeat-params", type=int, default=10)
    parser.add_argument("--num-students", type=int, default=20000)
    parser.add_argument("--base-seed", type=int, default=20280812)
    parser.add_argument("--no-rerun-missing", action="store_true")
    parser.add_argument("--force-rerun", action="store_true")
    parser.add_argument("--skip-if-panel", action="store_true")
    return parser.parse_args()


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    env.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")
    return env


def import_legacy_modules(legacy_code_dir: Path):
    legacy_code_dir = configure_overlay(legacy_code_dir)
    import pipeline  # type: ignore

    fancier_plots = import_legacy_file(
        "legacy_2020_fancier_plots_unaware_aa",
        legacy_code_dir / "visualization" / "fancier_plots.py",
    )
    plot_multiple_pareto_points_clean = fancier_plots.plot_multiple_pareto_points_clean

    return pipeline, plot_multiple_pareto_points_clean


def main_student_parameters(num_students: int) -> dict:
    return {
        "SIMULATION_TYPE": "SINGLE_SCHOOL",
        "NUM_STUDENTS": num_students,
        "CAPACITY": 0.2,
        "NUM_FEATURES": 2,
        "NUM_GROUPS": 2,
        "FRACTIONS_GROUPS": [0.5, 0.5],
        "TRUESKILL_DIST": ("NORMAL", 0, 1),
        "FEATURE_DIST": ("NORMAL", 0, 1),
        "FEATURE_DIST_A0": ("NORMAL", 0, 1),
        "FEATURE_DIST_A1": ("NORMAL", 0, 1),
        "FEATURE_DIST_B0": ("NORMAL", -4, 5),
        "FEATURE_DIST_B1": ("NORMAL", -4, 1),
    }


def school_parameters() -> dict:
    return {
        "NUM_SCHOOL_TYPES": 6,
        "CAPACITY": 0.2,
        "SKILL_ESTIMATION_FUNCTION_a": "normal_learning_aware",
        "ADMISSION_FUNCTION_a": "estimated_skill_ranking",
        "FEATURES_TO_USE_a": 0,
        "SKILL_ESTIMATION_FUNCTION_b": "normal_learning_unaware",
        "ADMISSION_FUNCTION_b": "estimated_skill_ranking",
        "FEATURES_TO_USE_b": 0,
        "SKILL_ESTIMATION_FUNCTION_c": "normal_learning_aware",
        "ADMISSION_FUNCTION_c": "estimated_skill_ranking_pergroup",
        "FEATURES_TO_USE_c": 0,
        "SKILL_ESTIMATION_FUNCTION_d": "normal_learning_aware",
        "ADMISSION_FUNCTION_d": "estimated_skill_ranking",
        "FEATURES_TO_USE_d": -1,
        "SKILL_ESTIMATION_FUNCTION_e": "normal_learning_unaware",
        "ADMISSION_FUNCTION_e": "estimated_skill_ranking",
        "FEATURES_TO_USE_e": -1,
        "SKILL_ESTIMATION_FUNCTION_f": "normal_learning_aware",
        "ADMISSION_FUNCTION_f": "estimated_skill_ranking_pergroup",
        "FEATURES_TO_USE_f": -1,
        "save_students_df": False,
        "FRAC_GROUPS_ADMIT_B": 0.5,
    }


def build_run_parameters(args: argparse.Namespace, tau: float) -> dict:
    run_params = copy.copy(main_student_parameters(args.num_students))
    run_params.update(school_parameters())
    run_params.update(
        {
            "FRAC_GROUPS_ADMIT_B": float(tau),
            "DO_STUDENT_BUDGETS": True,
            "PROB_MEETS_BUDGET_A": 1,
            "PROB_MEETS_BUDGET_B": 2 / 3,
        }
    )
    return run_params


def cache_path(args: argparse.Namespace) -> Path:
    path = args.cache_dir / f"{LABEL}_metrics.csv"
    gz_path = path.with_suffix(path.suffix + ".gz")
    if gz_path.exists() and not path.exists():
        return gz_path
    return path


def writable_cache_path(args: argparse.Namespace) -> Path:
    return args.cache_dir / f"{LABEL}_metrics.csv"


def tau_values() -> list[float]:
    values = list(np.linspace(0.01, 0.99, 25))
    values.append(0.5)
    return [float(value) for value in values]


def normalize_schools_df(schools_df: pd.DataFrame) -> pd.DataFrame:
    if "school_type" not in schools_df.columns:
        schools_df = schools_df.reset_index()
        if "index" in schools_df.columns and "school_type" not in schools_df.columns:
            schools_df = schools_df.rename(columns={"index": "school_type"})
    return schools_df.copy()


def generate_pareto_metrics(args: argparse.Namespace, pipeline) -> pd.DataFrame:
    rows = []
    for tau_index, tau in enumerate(tau_values()):
        for repeat in range(args.repeat_params):
            seed = args.base_seed + tau_index * 1000 + repeat
            random.seed(seed)
            np.random.seed(seed)
            _, schools_df, _ = pipeline.pipeline(build_run_parameters(args, tau))
            schools_df = normalize_schools_df(schools_df)
            schools_df["label"] = LABEL
            schools_df["FRAC_GROUPS_ADMIT_B"] = tau
            schools_df["repeat"] = repeat
            rows.append(schools_df)

    dff = pd.concat(rows, ignore_index=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    dff.to_csv(writable_cache_path(args), index=False)
    return dff


def load_or_generate_pareto_metrics(args: argparse.Namespace, pipeline) -> pd.DataFrame:
    path = cache_path(args)
    if path.exists() and not args.force_rerun:
        return pd.read_csv(path)
    if args.no_rerun_missing:
        raise FileNotFoundError(f"Missing {path}")
    return generate_pareto_metrics(args, pipeline)


def generate_if_panel(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        str(REPRO_ROOT / "scripts" / "replot_legacy_nonstrategic_from_2020.py"),
        "--figure-set",
        "unaware_aa_comparison",
        "--cache-dir",
        str(args.if_cache_dir),
        "--output-dir",
        str(args.output_dir),
    ]
    subprocess.run(command, cwd=REPO_ROOT, env=command_env(), check=True)


def plot_pareto(dff: pd.DataFrame, plot_multiple_pareto_points_clean, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    old_output_dir = os.environ.get(LEGACY_PLOTS_DIR_ENV)
    os.environ[LEGACY_PLOTS_DIR_ENV] = str(output_dir)
    try:
        plot_multiple_pareto_points_clean(
            dff,
            LABEL,
            schools_todo=["a", "b", "e", "d"],
            savenameappend="_withunaware",
            arrows=True,
        )
    finally:
        if old_output_dir is None:
            os.environ.pop(LEGACY_PLOTS_DIR_ENV, None)
        else:
            os.environ[LEGACY_PLOTS_DIR_ENV] = old_output_dir


def main() -> int:
    args = parse_args()
    pipeline, plot_multiple_pareto_points_clean = import_legacy_modules(args.legacy_code_dir)
    pareto_generated = False
    try:
        dff = load_or_generate_pareto_metrics(args, pipeline)
        plot_pareto(dff, plot_multiple_pareto_points_clean, args.output_dir)
        pareto_generated = True
    except FileNotFoundError:
        if not args.no_rerun_missing:
            raise
    if not args.skip_if_panel:
        generate_if_panel(args)
    if pareto_generated:
        print(args.output_dir / f"{LABEL}_differentpoliciescurves_withunaware.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
