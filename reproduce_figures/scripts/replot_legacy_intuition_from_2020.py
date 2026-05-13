#!/usr/bin/env python3
"""Reproduce Figure 2 intuition joint-distribution panels from 2020 code.

This is intentionally a small rerun wrapper: the original notebook generated
these panels directly from in-memory student-level outputs rather than from the
paperclean5 aggregate cache.
"""

from __future__ import annotations

import argparse
import copy
import os
import site
import sys
from pathlib import Path


USER_SITE = site.getusersitepackages()
sys.path = [path for path in sys.path if path != USER_SITE]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")

import matplotlib

matplotlib.use("Agg")
import numpy as np

from legacy_overlay import configure_overlay, import_legacy_file


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEGACY_CODE_DIR = REPO_ROOT / "reproduce_figures" / "legacy_code" / "2020_sims"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "reproduce_figures" / "workspace" / "generated" / "plots"
LEGACY_PLOTS_DIR_ENV = "MS_FIGURES_LEGACY_PLOTS_DIR"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-code-dir", type=Path, default=DEFAULT_LEGACY_CODE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--num-students", type=int, default=20000)
    parser.add_argument("--sample-per-group", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20280812)
    return parser.parse_args()


def import_legacy_modules(legacy_code_dir: Path):
    legacy_code_dir = configure_overlay(legacy_code_dir)
    import pipeline  # type: ignore

    fancier_plots = import_legacy_file(
        "legacy_2020_fancier_plots_intuition",
        legacy_code_dir / "visualization" / "fancier_plots.py",
    )
    plot_2d_estimate_thresholds = fancier_plots.plot_2d_estimate_thresholds

    return pipeline, plot_2d_estimate_thresholds


def base_parameters(num_students: int) -> dict[str, object]:
    main_student_parameters = {
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
    school_parameters = {
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
    params = copy.copy(main_student_parameters)
    params.update(school_parameters)
    return params


def run_and_plot(pipeline, plot_2d_estimate_thresholds, params: dict[str, object], label: str, output_dir: Path, sample_per_group: int, include_test_free: bool) -> None:
    students_df, schools_df, _ = pipeline.pipeline(params)

    output_dir.mkdir(parents=True, exist_ok=True)
    old_output_dir = os.environ.get(LEGACY_PLOTS_DIR_ENV)
    os.environ[LEGACY_PLOTS_DIR_ENV] = str(output_dir)
    try:
        plot_2d_estimate_thresholds(
            "a",
            schools_df,
            students_df,
            label,
            numeach=sample_per_group,
            ymin=-3,
            ymax=3,
            scale_kdw=1.5,
            do_legend=(label == "simulations_2d_skillestimates_nobudget"),
        )
        if include_test_free:
            plot_2d_estimate_thresholds(
                "d",
                schools_df,
                students_df,
                label,
                numeach=sample_per_group,
                ymin=-3,
                ymax=3,
                scale_kdw=1.5,
            )
    finally:
        if old_output_dir is None:
            os.environ.pop(LEGACY_PLOTS_DIR_ENV, None)
        else:
            os.environ[LEGACY_PLOTS_DIR_ENV] = old_output_dir


def main() -> int:
    args = parse_args()
    np.random.seed(args.seed)
    pipeline, plot_2d_estimate_thresholds = import_legacy_modules(args.legacy_code_dir)

    no_barrier = base_parameters(args.num_students)
    run_and_plot(
        pipeline,
        plot_2d_estimate_thresholds,
        no_barrier,
        "simulations_2d_skillestimates_nobudget",
        args.output_dir,
        args.sample_per_group,
        include_test_free=False,
    )

    barrier = base_parameters(args.num_students)
    barrier.update({"PROB_MEETS_BUDGET_A": 1, "PROB_MEETS_BUDGET_B": 2 / 3.0, "DO_STUDENT_BUDGETS": True})
    run_and_plot(
        pipeline,
        plot_2d_estimate_thresholds,
        barrier,
        "simulations_2d_skillestimates_barrier",
        args.output_dir,
        args.sample_per_group,
        include_test_free=True,
    )

    for name in [
        "simulations_2d_skillestimates_nobudget_2dskilldist_testbased.pdf",
        "simulations_2d_skillestimates_barrier_2dskilldist_testbased.pdf",
        "simulations_2d_skillestimates_barrier_2dskilldist_testfree.pdf",
    ]:
        print(args.output_dir / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
