#!/usr/bin/env python3
"""Regenerate legacy non-strategic cache labels for Figures 3, 4, and 9.

This wraps the traced 2020 notebook simulation grids in a concise script. It
writes local paperclean5-shaped CSV caches, then calls the existing cache-based
replot wrapper against those fresh CSVs.
"""

from __future__ import annotations

import argparse
import copy
import os
import random
import site
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path


USER_SITE = site.getusersitepackages()
sys.path = [path for path in sys.path if path != USER_SITE]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")

import numpy as np
import pandas as pd

from legacy_overlay import configure_overlay


REPO_ROOT = Path(__file__).resolve().parents[2]
REPRO_ROOT = REPO_ROOT / "reproduce_figures"
DEFAULT_LEGACY_CODE_DIR = REPO_ROOT / "reproduce_figures" / "legacy_code" / "2020_sims"
DEFAULT_CACHE_ROOT = REPO_ROOT / "reproduce_figures" / "workspace" / "cache" / "legacy_nonstrategic_rerun"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "plots"
PARAM_FILE = "params_run_paperclean5.csv"
METRICS_FILE = "run_metrics_schools_paperclean5.csv"
_LEGACY_PIPELINE = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--figure-set",
        choices=["variance_and_barrier", "fairness", "two_dimensional_differences", "all"],
        default="all",
    )
    parser.add_argument("--legacy-code-dir", type=Path, default=DEFAULT_LEGACY_CODE_DIR)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--num-students", type=int, default=20000)
    parser.add_argument("--n-processes", type=int, default=1)
    parser.add_argument("--base-seed", type=int, default=20280812)
    parser.add_argument("--force-rerun", action="store_true")
    return parser.parse_args()


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    env.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")
    return env


def import_legacy_pipeline(legacy_code_dir: Path):
    configure_overlay(legacy_code_dir)
    import pipeline  # type: ignore

    return pipeline


def init_legacy_worker(legacy_code_dir: Path) -> None:
    global _LEGACY_PIPELINE
    _LEGACY_PIPELINE = import_legacy_pipeline(legacy_code_dir)


def cache_dir(args: argparse.Namespace) -> Path:
    if args.cache_dir is not None:
        return args.cache_dir
    return DEFAULT_CACHE_ROOT / args.figure_set


def cache_files(args: argparse.Namespace) -> tuple[Path, Path]:
    root = cache_dir(args)
    return root / PARAM_FILE, root / METRICS_FILE


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


def equivariance_value() -> float:
    return ((1**-1 + 1**-1) - (5) ** -1) ** -1


def variance_values() -> list[tuple[str, float, float]]:
    values = [("NORMAL", -1, float(var)) for var in np.linspace(0.01, 3, 20)]
    values.append(("NORMAL", -1, equivariance_value()))
    return values


def copy_with_updates(params: dict, updates: dict) -> dict:
    result = copy.deepcopy(params)
    result.update(updates)
    return result


def iter_single(params: dict, vary_parameter: str, values: list, repeat_params: int):
    for _ in range(repeat_params):
        for value in values:
            yield copy_with_updates(params, {vary_parameter: value})


def iter_double_variance_together(params: dict, values1: list, values2: list, repeat_params: int):
    for _ in range(repeat_params):
        for value1 in values1:
            for value2 in values2:
                run_params = copy.deepcopy(params)
                run_params["FEATURE_DIST_A1"] = value1
                run_params["FEATURE_DIST_B1"] = value1
                run_params["PROB_MEETS_BUDGET_B"] = float(value2)
                yield run_params


def iter_nonevary(params: dict, repeat_params: int):
    for _ in range(repeat_params):
        yield copy.deepcopy(params)


def figure_generators(args: argparse.Namespace) -> list[tuple[str, str, object]]:
    main_params = main_student_parameters(args.num_students)
    school_params = school_parameters()
    selected = []

    if args.figure_set in {"variance_and_barrier", "all"}:
        selected.append(
            (
                "simulations_vary_feature1_var_update",
                "variance_and_barrier",
                iter_single(main_params, "FEATURE_DIST_B1", variance_values(), repeat_params=100),
            )
        )
        equal_student_parameters = copy_with_updates(
            main_params,
            {
                "FEATURE_DIST_B0": ("NORMAL", -4, 1),
                "FEATURE_DIST_B1": ("NORMAL", -4, 1),
                "PROB_MEETS_BUDGET_A": 1,
                "DO_STUDENT_BUDGETS": True,
            },
        )
        selected.append(
            (
                "simulations_vary_barrier",
                "variance_and_barrier",
                iter_single(
                    equal_student_parameters,
                    "PROB_MEETS_BUDGET_B",
                    [float(value) for value in np.linspace(0, 1, 20)],
                    repeat_params=100,
                ),
            )
        )

    if args.figure_set in {"two_dimensional_differences", "all"}:
        run_params_varyboth = copy_with_updates(
            copy_with_updates(main_params, school_params),
            {
                "PROB_MEETS_BUDGET_A": 1,
                "DO_STUDENT_BUDGETS": True,
            },
        )
        selected.append(
            (
                "simulations_vary_feature1_and_disbudget",
                "two_dimensional_differences",
                iter_double_variance_together(
                    run_params_varyboth,
                    variance_values(),
                    [float(value) for value in np.linspace(0, 1, 20)],
                    repeat_params=10,
                ),
            )
        )

    if args.figure_set in {"fairness", "all"}:
        fairness_params = copy_with_updates(
            copy_with_updates(main_params, school_params),
            {
                "save_students_df": False,
                "FRAC_GROUPS_ADMIT_B": 0.5,
                "DO_STUDENT_BUDGETS": True,
                "PROB_MEETS_BUDGET_A": 1,
                "PROB_MEETS_BUDGET_B": 2 / 3,
            },
        )
        selected.append(
            (
                "paper_budgetsimulations_forstudentIF_update4",
                "fairness",
                iter_nonevary(fairness_params, repeat_params=400),
            )
        )

    return selected


def normalize_school_metrics(schools_df: pd.DataFrame, label: str, runhash: str, save_students: bool) -> pd.DataFrame:
    metrics = schools_df.copy()
    if not save_students and "admitted_students" in metrics.columns:
        metrics = metrics.drop(columns=["admitted_students"])
    metrics["label"] = label
    metrics["hash"] = runhash
    return metrics


def iter_simulation_tasks(args: argparse.Namespace):
    run_index = 0
    for label, _, generator in figure_generators(args):
        for params in generator:
            yield run_index, label, copy.deepcopy(params), args.base_seed + run_index
            run_index += 1


def run_simulation_task(task):
    run_index, label, params, seed = task
    if _LEGACY_PIPELINE is None:
        raise RuntimeError("Legacy pipeline was not initialized.")
    random.seed(seed)
    np.random.seed(seed)
    _, schools_df, out_params = _LEGACY_PIPELINE.pipeline(copy.deepcopy(params))
    runhash = f"{label}_{run_index:06d}"
    out_params = copy.deepcopy(out_params)
    out_params["label"] = label
    out_params["hash"] = runhash
    metrics = normalize_school_metrics(
        schools_df,
        label,
        runhash,
        save_students=bool(out_params.get("save_students_df", False)),
    )
    return run_index, out_params, metrics


def generate_cache(args: argparse.Namespace) -> None:
    param_file, metrics_file = cache_files(args)
    if param_file.exists() and metrics_file.exists() and not args.force_rerun:
        return

    tasks = list(iter_simulation_tasks(args))
    results = []
    if args.n_processes > 1:
        with Pool(args.n_processes, initializer=init_legacy_worker, initargs=(args.legacy_code_dir,)) as pool:
            for result in pool.imap_unordered(run_simulation_task, tasks):
                results.append(result)
                if len(results) % 100 == 0:
                    print(f"generated {len(results)} simulations")
    else:
        init_legacy_worker(args.legacy_code_dir)
        for task in tasks:
            results.append(run_simulation_task(task))
            if len(results) % 100 == 0:
                print(f"generated {len(results)} simulations")

    results.sort(key=lambda result: result[0])
    params_rows = [out_params for _, out_params, _ in results]
    metrics_frames = [metrics for _, _, metrics in results]

    param_file.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(params_rows).to_csv(param_file, index=False)
    pd.concat(metrics_frames, ignore_index=True).to_csv(metrics_file, index=False)


def replot(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        str(REPRO_ROOT / "scripts" / "replot_legacy_nonstrategic_from_2020.py"),
        "--figure-set",
        args.figure_set,
        "--legacy-code-dir",
        str(args.legacy_code_dir),
        "--cache-dir",
        str(cache_dir(args)),
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
