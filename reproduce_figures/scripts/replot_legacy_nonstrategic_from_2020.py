#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
import os
import site
import sys
from pathlib import Path

USER_SITE = site.getusersitepackages()
sys.path = [p for p in sys.path if p != USER_SITE]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import pandas as pd

from legacy_overlay import configure_overlay, import_legacy_file


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEGACY_CODE_DIR = REPO_ROOT / "reproduce_figures" / "legacy_code" / "2020_sims"
DEFAULT_CACHE_DIR = REPO_ROOT / "reproduce_figures" / "inputs"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "reproduce_figures" / "workspace" / "generated" / "plots"
LEGACY_PLOTS_DIR_ENV = "MS_FIGURES_LEGACY_PLOTS_DIR"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replot legacy 2020 non-strategic paper figures from cached paperclean5 tables."
    )
    parser.add_argument(
        "--figure-set",
        choices=[
            "variance_and_barrier",
            "fairness",
            "two_dimensional_differences",
            "unaware_aa_comparison",
            "all",
        ],
        default="all",
    )
    parser.add_argument("--legacy-code-dir", type=Path, default=DEFAULT_LEGACY_CODE_DIR)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def import_legacy_modules(legacy_code_dir: Path):
    legacy_code_dir = configure_overlay(legacy_code_dir)
    import save_results  # type: ignore
    import helpers  # type: ignore
    fancier_plots = import_legacy_file(
        "legacy_2020_fancier_plots_nonstrategic",
        legacy_code_dir / "visualization" / "fancier_plots.py",
        legacy_dependency_prefixes=("generic", "visualization"),
    )
    indiv_fairness = import_legacy_file(
        "legacy_2020_indivfairness_nonstrategic",
        legacy_code_dir / "visualization" / "IndivFairness.py",
        legacy_dependency_prefixes=("generic", "visualization"),
    )
    return save_results, helpers, fancier_plots, indiv_fairness


def cache_csv(path: Path) -> Path:
    if path.exists():
        return path
    gz_path = path.with_suffix(path.suffix + ".gz")
    if gz_path.exists():
        return gz_path
    return path


def load_legacy_results(cache_dir: Path, save_results, helpers):
    del save_results
    param_file = cache_csv(cache_dir / "params_run_paperclean5.csv")
    metrics_file = cache_csv(cache_dir / "run_metrics_schools_paperclean5.csv")
    if not param_file.exists() or not metrics_file.exists():
        raise FileNotFoundError("Missing migrated paperclean5 CSV inputs")

    target_labels = {
        "simulations_vary_feature1_var",
        "simulations_vary_feature1_var_7",
        "simulations_vary_feature1_var_update",
        "simulations_vary_barrier",
        "simulations_vary_feature1_and_disbudget",
        "paper_budgetsimulations_forstudentIF_update4",
    }
    metric_cols = [
        "hash",
        "label",
        "school_type",
        "frac_A",
        "frac_B",
        "avgadmittedskill_A",
        "avgadmittedskill_B",
        "avgadmittedskill",
        "IF",
        "IF_rawskill",
    ]
    metrics_iter = pd.read_csv(metrics_file, usecols=metric_cols, chunksize=200000, low_memory=False)
    metrics_frames = [chunk[chunk["label"].isin(target_labels)].copy() for chunk in metrics_iter]
    metricdf = pd.concat(metrics_frames, ignore_index=True)

    param_cols = ["hash", "FEATURE_DIST_B1", "PROB_MEETS_BUDGET_B"]
    paramdf = pd.read_csv(param_file, usecols=param_cols, low_memory=False)

    def safe_eval(value):
        if isinstance(value, str):
            return ast.literal_eval(value)
        return value

    paramdf["FEATURE_DIST_B1"] = paramdf["FEATURE_DIST_B1"].apply(safe_eval)
    dff = metricdf.merge(paramdf, on="hash", how="left")
    dff["IF_rawskill"] = dff["IF_rawskill"].where(dff["IF_rawskill"].notna(), dff["IF"])
    helpers.separate_distribution_column(dff, "FEATURE_DIST_B1")
    return dff


def resolve_label(dff, *labels):
    for label in labels:
        if not dff.query("label == @label").empty:
            return label
    raise ValueError(f"None of these labels exist in the migrated cache: {labels}")


def resolve_label_with_metric(dff, metric: str, *labels):
    for label in labels:
        if not dff.query("label == @label").dropna(subset=[metric]).empty:
            return label
    raise ValueError(f"None of these labels have non-missing {metric}: {labels}")


def run_in_legacy_plots_dir(output_dir: Path, callback) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    old_output_dir = os.environ.get(LEGACY_PLOTS_DIR_ENV)
    os.environ[LEGACY_PLOTS_DIR_ENV] = str(output_dir)
    try:
        callback()
    finally:
        if old_output_dir is None:
            os.environ.pop(LEGACY_PLOTS_DIR_ENV, None)
        else:
            os.environ[LEGACY_PLOTS_DIR_ENV] = old_output_dir


def legacy_save_line_plot(fancier_plots, output_dir: Path, name: str, callback) -> None:
    def make_plot() -> None:
        plt.figure()
        callback()
        fancier_plots.saveimage(name, close=True)

    run_in_legacy_plots_dir(output_dir, make_plot)
    print(output_dir / f"{name}.pdf")


def legacy_save_if_plot(
    indiv_fairness,
    output_dir: Path,
    dff,
    label: str,
    xvarlabel: str,
    ifcol: str,
    equivariance=None,
    output_label: str | None = None,
    true_skill_range: tuple[float, float] | None = None,
) -> None:
    plot_label = output_label or label
    if output_label is not None and output_label != label:
        plot_dff = dff[dff["label"] == label].copy()
        plot_dff.loc[:, "label"] = output_label
    else:
        plot_dff = dff

    def make_plot() -> None:
        plt.figure()
        indiv_fairness.plot_2d_IF(
            plot_dff,
            plot_label,
            equivariance=equivariance,
            xvarlabel=xvarlabel,
            IFcol=ifcol,
            true_skill_range=true_skill_range,
        )
        plt.close()

    run_in_legacy_plots_dir(output_dir, make_plot)
    print(output_dir / f"{plot_label}_2dIF_{xvarlabel}.pdf")


def legacy_save_individual_fairness_plot(
    indiv_fairness,
    output_dir: Path,
    dff,
    label: str,
    school_names: dict[str, str],
    schoolorder: list[str],
    ifcol: str = "IF_rawskill",
    savenameappend: str = "",
    legend_offset: float = 1.1,
) -> None:
    school_types = list(school_names)

    def make_plot() -> None:
        plt.figure()
        indiv_fairness.plot_individual_fairness_curves_clean(
            dff[dff["school_type"].isin(school_types)].copy(),
            label,
            school_names=school_names,
            schoolorder=schoolorder,
            IFcol=ifcol,
            savenameappend=savenameappend,
            legend_offset=legend_offset,
        )
        plt.close()

    run_in_legacy_plots_dir(output_dir, make_plot)
    print(output_dir / f"{label}_indivfairness{savenameappend}.pdf")


def legacy_save_2d_difference_heatmap(
    fancier_plots,
    output_dir: Path,
    dff,
    label: str,
    metric: str,
    schools: tuple[str, str] = ("a", "d"),
    vmin: float | None = None,
    vmax: float | None = None,
    y_min: float | None = None,
) -> None:
    def make_plot() -> None:
        plt.figure()
        fancier_plots.plot_2dheatmap_diff(dff, label, z=metric, schools=list(schools), vmin=vmin, vmax=vmax, y_min=y_min)
        plt.close()

    run_in_legacy_plots_dir(output_dir, make_plot)
    print(output_dir / f"{label}_2ddifference_{metric}.pdf")


def generate_variance_and_barrier_figures(dff, output_dir, fancier_plots, indiv_fairness):
    equivariance = ((1 ** -1 + 1 ** -1) - (5) ** -1) ** -1

    source_label = resolve_label(
        dff,
        "simulations_vary_feature1_var_update",
        "simulations_vary_feature1_var_7",
        "simulations_vary_feature1_var",
    )
    if_source_label = resolve_label_with_metric(
        dff,
        "IF_rawskill",
        "simulations_vary_feature1_var_update",
        "simulations_vary_feature1_var_7",
        "simulations_vary_feature1_var",
    )
    output_label = "simulations_vary_feature1_var_update"
    legacy_save_line_plot(
        fancier_plots,
        output_dir,
        f"{output_label}_frac",
        lambda: fancier_plots.plot_group_features_by_param(
            dff, source_label, "frac", "FEATURE_DIST_B1_var", "a", legend=False, equivariance=equivariance
        ),
    )
    legacy_save_line_plot(
        fancier_plots,
        output_dir,
        f"{output_label}_avgadmittedskill",
        lambda: fancier_plots.plot_group_features_by_param(
            dff, source_label, "avgadmittedskill", "FEATURE_DIST_B1_var", "a", legend=True, equivariance=equivariance
        ),
    )
    legacy_save_if_plot(
        indiv_fairness,
        output_dir,
        dff,
        if_source_label,
        "FEATURE_DIST_B1_var",
        "IF_rawskill",
        equivariance=equivariance,
        output_label=output_label,
        true_skill_range=(0, 3),
    )

    label = "simulations_vary_barrier"
    legacy_save_line_plot(
        fancier_plots,
        output_dir,
        f"{label}_frac_PROB_MEETS_BUDGET_B",
        lambda: fancier_plots.plot_group_features_by_param(dff, label, "frac", "PROB_MEETS_BUDGET_B", "a", legend=False, equivariance=None),
    )
    legacy_save_line_plot(
        fancier_plots,
        output_dir,
        f"{label}_avgadmittedskill_PROB_MEETS_BUDGET_B",
        lambda: fancier_plots.plot_group_features_by_param(
            dff, label, "avgadmittedskill", "PROB_MEETS_BUDGET_B", "a", legend=False, equivariance=None
        ),
    )
    legacy_save_if_plot(indiv_fairness, output_dir, dff, label, "PROB_MEETS_BUDGET_B", "IF_rawskill", true_skill_range=(0, 3))


def generate_2d_difference_heatmaps(dff, output_dir, fancier_plots):
    label = resolve_label(dff, "simulations_vary_feature1_and_disbudget")
    metrics = ["avgadmittedskill", "frac_B", "avgadmittedskill_A", "avgadmittedskill_B"]
    for metric in metrics:
        y_min = 0.05 if metric == "avgadmittedskill_B" else None
        legacy_save_2d_difference_heatmap(fancier_plots, output_dir, dff, label, metric, vmin=-0.6, vmax=0.6, y_min=y_min)


def generate_fairness_figures(dff, output_dir, indiv_fairness):
    label = "paper_budgetsimulations_forstudentIF_update4"
    dfloc = dff.query("label == @label").copy()
    legacy_save_individual_fairness_plot(
        indiv_fairness,
        output_dir,
        dfloc,
        label,
        school_names={
            "a": "Without Affirmative Action, test-based",
            "d": "Without Affirmative Action, test-free",
            "c": "Affirmative Action level $\\tau=.5$, test-based",
            "f": "Affirmative Action level $\\tau=.5$, test-free",
        },
        schoolorder=["Without Affirmative Action", "Affirmative Action level $\\tau=.5$"],
        savenameappend="",
        legend_offset=1.25,
    )
    legacy_save_individual_fairness_plot(
        indiv_fairness,
        output_dir,
        dfloc,
        label,
        school_names={
            "a": "Without Affirmative Action, test-based",
            "d": "Without Affirmative Action, test-free",
        },
        schoolorder=["Without Affirmative Action"],
        savenameappend="_withoutAA",
        legend_offset=1.25,
    )
    legacy_save_individual_fairness_plot(
        indiv_fairness,
        output_dir,
        dfloc,
        label,
        school_names={
            "a": "Without Affirmative Action, test-based",
            "b": "Unaware estimation (without Affirmative Action), test-based",
            "d": "Without Affirmative Action, test-free",
            "e": "Unaware estimation (without Affirmative Action), test-free",
            "c": "Affirmative Action level $\\tau=.5$, test-based",
            "f": "Affirmative Action level $\\tau=.5$, test-free",
        },
        schoolorder=[
            "Unaware estimation (without Affirmative Action)",
            "Without Affirmative Action",
            "Affirmative Action level $\\tau=.5$",
        ],
        savenameappend="_withunaware",
        legend_offset=1.35,
    )
    legacy_save_individual_fairness_plot(
        indiv_fairness,
        output_dir,
        dfloc,
        label,
        school_names={
            "a": "Aware estimation, test-based",
            "b": "Unaware estimation, test-based",
            "d": "Aware estimation, test-free",
            "e": "Unaware estimation, test-free",
        },
        schoolorder=["Unaware estimation", "Aware estimation"],
        savenameappend="_withunaware_noAA",
        legend_offset=1.25,
    )


def main():
    args = parse_args()
    os.chdir(REPO_ROOT)
    save_results, helpers, fancier_plots, indiv_fairness = import_legacy_modules(args.legacy_code_dir)
    dff = load_legacy_results(args.cache_dir, save_results, helpers)
    if args.figure_set in {"variance_and_barrier", "all"}:
        generate_variance_and_barrier_figures(dff, args.output_dir, fancier_plots, indiv_fairness)
    if args.figure_set in {"fairness", "all"}:
        generate_fairness_figures(dff, args.output_dir, indiv_fairness)
    if args.figure_set in {"two_dimensional_differences", "all"}:
        generate_2d_difference_heatmaps(dff, args.output_dir, fancier_plots)
    if args.figure_set in {"unaware_aa_comparison", "all"}:
        generate_fairness_figures(dff, args.output_dir, indiv_fairness)


if __name__ == "__main__":
    main()
