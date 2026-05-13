#!/usr/bin/env python3
"""Reproduce calibrated THEOP figures from checked-in fitted parameters.

This script deliberately does not read restricted THEOP microdata. It expects
the fitted calibration numbers to be checked into
reproduce_figures/inputs/calibrated_theop_fit_params.json, then uses those values as
synthetic-student simulation inputs.

Default behavior:

1. run any missing synthetic simulations into the configured cache directory;
2. aggregate the cached results;
3. save the six calibrated paper PNGs.

Use --plots-only to skip simulation runs and plot from an existing cache.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import site
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = "reproduce_figures/inputs/calibrated_theop_fit_params.json"
USER_SITE = site.getusersitepackages()
sys.path = [path for path in sys.path if path != USER_SITE]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")
METRICS = [
    "frac_A",
    "frac_B",
    "avgadmittedskill_A",
    "avgadmittedskill_B",
    "avgadmittedskill",
    "p_apply_",
    "if_gap",
]
METRICS_B = ["frac_B", "avgadmittedskill_B"]
METRIC_NAME_MAP = {
    "frac_B": r"$\tau$, Diversity level",
    "avgadmittedskill": "Avg admitted skill",
    "avgadmittedskill_A": r"Avg admitted skill, Group $A$",
    "avgadmittedskill_B": r"Avg admitted skill, Group $B$",
    "if_gap": "Individual fairness gap",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_repo_path(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return repo_root() / path


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"Config must contain a JSON object: {path}")
    return config


def iter_missing_values(value: Any, prefix: str = "") -> list[str]:
    missing: list[str] = []
    if value is None:
        return [prefix or "<root>"]
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            missing.extend(iter_missing_values(child, child_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            missing.extend(iter_missing_values(child, child_prefix))
    return missing


def validate_config(config: dict[str, Any]) -> None:
    missing = iter_missing_values(config)
    empty_required = []

    simulation = config.get("simulation", {})
    if not isinstance(simulation, dict):
        raise ValueError("simulation must be an object")
    if not simulation.get("base_parameters"):
        empty_required.append("simulation.base_parameters")

    scenario_grids = config.get("scenario_grids", {})
    if not isinstance(scenario_grids, dict):
        raise ValueError("scenario_grids must be an object")
    strategic_cost = scenario_grids.get("strategic_cost", {})
    nonstrategic_barrier = scenario_grids.get("nonstrategic_barrier", {})
    if strategic_cost.get("enabled", False):
        if not grid_values(strategic_cost.get("cost_A_values")):
            empty_required.append("scenario_grids.strategic_cost.cost_A_values")
        if not grid_values(strategic_cost.get("cost_B_values")):
            empty_required.append("scenario_grids.strategic_cost.cost_B_values")
    if nonstrategic_barrier.get("enabled", False):
        if not grid_values(nonstrategic_barrier.get("prob_meets_budget_A_values")):
            empty_required.append("scenario_grids.nonstrategic_barrier.prob_meets_budget_A_values")
        if not grid_values(nonstrategic_barrier.get("prob_meets_budget_B_values")):
            empty_required.append("scenario_grids.nonstrategic_barrier.prob_meets_budget_B_values")

    if missing or empty_required:
        lines = ["Fit-parameter config is incomplete."]
        if missing:
            lines.append("Missing null-valued fields:")
            lines.extend(f"  {item}" for item in missing)
        if empty_required:
            lines.append("Missing empty required fields:")
            lines.extend(f"  {item}" for item in empty_required)
        raise ValueError("\n".join(lines))


def grid_values(spec: Any) -> list[float]:
    if spec is None:
        return []
    if isinstance(spec, list):
        return sorted({round(float(value), 3) for value in spec})
    if isinstance(spec, dict):
        import numpy as np

        start = float(spec["start"])
        stop = float(spec["stop"])
        step = float(spec["step"])
        round_digits = int(spec.get("round_digits", 3))
        values = np.arange(start, stop + step / 10, step).round(round_digits).tolist()
        values.extend(round(float(value), round_digits) for value in spec.get("extra", []))
        return sorted(set(values))
    return [round(float(spec), 3)]


def format_number(value: float) -> str:
    return str(float(value))


def normalize_params(value: Any) -> Any:
    if isinstance(value, list):
        if value and isinstance(value[0], str) and value[0] == "NORMAL":
            return tuple(value)
        return [normalize_params(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_params(child) for key, child in value.items()}
    return value


def feature_distribution_params(calibration: dict[str, Any]) -> dict[str, Any]:
    features = calibration["features"]
    distributions = calibration["feature_distributions"]
    params: dict[str, Any] = {"NUM_FEATURES": len(features)}

    for index, feature in enumerate(features):
        for group in ("A", "B"):
            spec = distributions[group][feature]
            params[f"FEATURE_DIST_{group}{index}"] = (
                "NORMAL",
                spec["mean"],
                spec["variance"],
            )

    return params


def info_base_parameters(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    base_parameters = normalize_params(config["simulation"]["base_parameters"])
    calibrations = config["calibrations"]
    result: dict[str, dict[str, Any]] = {}

    for info_type, calibration in calibrations.items():
        params = deepcopy(base_parameters)
        params.update(feature_distribution_params(calibration))
        result[info_type] = params

    return result


def build_parameter_sets(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    n_runs = int(config["simulation"]["num_runs"])
    scenario_grids = config["scenario_grids"]
    base_by_info = info_base_parameters(config)
    parameter_sets: dict[str, dict[str, Any]] = {}

    strategic_cost = scenario_grids["strategic_cost"]
    if strategic_cost.get("enabled", False):
        cost_a_values = grid_values(strategic_cost["cost_A_values"])
        if len(cost_a_values) != 1:
            raise ValueError("The calibrated notebook assumes exactly one group-A cost value.")
        cost_a = cost_a_values[0]
        for info_type, info_params in base_by_info.items():
            for run_index in range(n_runs):
                for cost_b in grid_values(strategic_cost["cost_B_values"]):
                    params = deepcopy(info_params)
                    params["SIMULATION_TYPE"] = "SINGLE_SCHOOL_COST_MODEL"
                    params["STUDENT_TEST_COST"] = {"A": cost_a, "B": cost_b}
                    name = f"{info_type}_info_costmodel_costB_{format_number(cost_b)}_run_{run_index}"
                    parameter_sets[name] = params

    nonstrategic_barrier = scenario_grids["nonstrategic_barrier"]
    if nonstrategic_barrier.get("enabled", False):
        prob_a_values = grid_values(nonstrategic_barrier["prob_meets_budget_A_values"])
        if len(prob_a_values) != 1:
            raise ValueError("The calibrated notebook assumes exactly one group-A barrier value.")
        prob_a = prob_a_values[0]
        for info_type, info_params in base_by_info.items():
            for run_index in range(n_runs):
                for prob_b in grid_values(nonstrategic_barrier["prob_meets_budget_B_values"]):
                    params = deepcopy(info_params)
                    params["SIMULATION_TYPE"] = "SINGLE_SCHOOL"
                    params["PROB_MEETS_BUDGET_A"] = prob_a
                    params["PROB_MEETS_BUDGET_B"] = prob_b
                    params["DO_STUDENT_BUDGETS"] = True
                    name = f"{info_type}_info_barriermodel__barrierB_{format_number(prob_b)}_run_{run_index}"
                    parameter_sets[name] = params

    return parameter_sets


def save_frame(frame: Any, path: Path) -> None:
    if hasattr(frame, "to_csv"):
        frame.to_csv(path)
        return
    if isinstance(frame, dict):
        import pandas as pd

        pd.Series(frame).to_csv(path)
        return
    raise TypeError(f"Object does not support to_csv: {type(frame)!r}")


def run_simulations(config: dict[str, Any], overwrite: bool = False, dry_run: bool = False) -> None:
    parameter_sets = build_parameter_sets(config)
    output_root = resolve_repo_path(config["simulation"]["output_root"])

    missing = [name for name in parameter_sets if overwrite or not (output_root / name).is_dir()]
    print(f"Prepared {len(parameter_sets)} calibrated THEOP parameter sets.")
    print(f"Simulation directories to create: {len(missing)}.")
    if dry_run:
        for name in missing[:20]:
            print(name)
        if len(missing) > 20:
            print(f"... {len(missing) - 20} more")
        return

    import pipeline

    output_root.mkdir(parents=True, exist_ok=True)
    for name in missing:
        instance_dir = output_root / name
        instance_dir.mkdir(parents=True, exist_ok=True)
        params = parameter_sets[name]

        students_df, schools_df, params_df = pipeline.pipeline(params)
        save_frame(students_df, instance_dir / "students_df.csv")
        save_frame(schools_df, instance_dir / "schools_df.csv")
        save_frame(params_df, instance_dir / "params_df.csv")

        params_no_test = deepcopy(params)
        params_no_test["SIMULATION_TYPE"] = "SINGLE_SCHOOL"
        params_no_test["FEATURES_TO_USE_a"] = -1
        drop_students_df, drop_schools_df, drop_params_df = pipeline.pipeline(params_no_test)
        save_frame(drop_students_df, instance_dir / "drop_students_df.csv")
        save_frame(drop_schools_df, instance_dir / "drop_schools_df.csv")
        save_frame(drop_params_df, instance_dir / "drop_params_df.csv")


def read_bool_series(series: Any) -> Any:
    if str(series.dtype) == "bool":
        return series
    return series.map(lambda value: str(value).lower() == "true")


def read_cached_results(config: dict[str, Any]) -> dict[str, Any]:
    import pandas as pd

    output_root = resolve_repo_path(config["simulation"]["output_root"])
    roundmult = int(config["simulation"]["skill_bin_roundmult"])
    instances = sorted(path.name for path in output_root.iterdir() if path.is_dir())

    schools: dict[str, Any] = {}
    students: dict[str, Any] = {}
    drop_schools: dict[str, dict[str, Any]] = {"high": {}, "low": {}}

    cost_pattern = re.compile(r"([^_]+)_info_costmodel_costB_([^_]+)_run_([^_]+)$")
    barrier_pattern = re.compile(r"([^_]+)_info_barriermodel__barrierB_([^_]+)_run_([^_]+)$")

    for instance in instances:
        if not cost_pattern.search(instance) and not barrier_pattern.search(instance):
            continue
        directory = output_root / instance
        info_type = instance.split("_info_", 1)[0]

        school_df = pd.read_csv(directory / "schools_df.csv")
        student_df = pd.read_csv(directory / "students_df.csv")
        if "take_test_at_threshold" in student_df:
            student_df["take_test_at_threshold"] = read_bool_series(student_df["take_test_at_threshold"])
        if "admitted" in student_df:
            student_df["admitted"] = read_bool_series(student_df["admitted"])
        student_df.loc[:, "skillcut_coarse"] = (
            (student_df.skill.rank(pct=True) * roundmult).round(1) / roundmult
        )

        schools[instance] = school_df
        students[instance] = student_df
        drop_schools[info_type][instance] = pd.read_csv(directory / "drop_schools_df.csv")

    return {
        "instances": instances,
        "schools": schools,
        "students": students,
        "drop_schools": drop_schools,
    }


def build_metric_frames(config: dict[str, Any], cached: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import pandas as pd

    n_runs = int(config["simulation"]["num_runs"])
    cost_values = grid_values(config["scenario_grids"]["strategic_cost"]["cost_B_values"])
    barrier_values = grid_values(config["scenario_grids"]["nonstrategic_barrier"]["prob_meets_budget_B_values"])
    schools = cached["schools"]
    students = cached["students"]

    metrics_df_cost: dict[str, dict[str, Any]] = {"high": {}, "low": {}}
    metrics_df_barrier: dict[str, dict[str, Any]] = {"high": {}, "low": {}}

    for info_type in ["high", "low"]:
        metrics_df_cost[info_type]["p_apply_A"] = {}
        metrics_df_cost[info_type]["p_apply_B"] = {}

        for metric in METRICS:
            metrics_df_cost[info_type][metric] = {}
            for cost in cost_values:
                metrics_df_cost[info_type][metric][cost] = {}
                for run_index in range(n_runs):
                    instance = f"{info_type}_info_costmodel_costB_{format_number(cost)}_run_{run_index}"
                    student_df = students[instance]
                    if metric == "p_apply_":
                        for group in ["A", "B"]:
                            group_students = student_df.query("group == @group")
                            metrics_df_cost[info_type][metric + group].setdefault(cost, {})[run_index] = group_students[
                                "take_test_at_threshold"
                            ].mean()
                    elif metric == "if_gap":
                        metrics_df_cost[info_type][metric][cost][run_index] = (
                            student_df.query('group == "A"').groupby("skillcut_coarse")["admitted"].mean()
                            - student_df.query('group == "B"').groupby("skillcut_coarse")["admitted"].mean()
                        )
                    elif metric in METRICS_B and len(student_df.query('group == "B" and take_test_at_threshold == True')) == 0:
                        metrics_df_cost[info_type][metric][cost][run_index] = 0
                    else:
                        metrics_df_cost[info_type][metric][cost][run_index] = schools[instance][metric].iloc[0]

            if metric != "p_apply_":
                metrics_df_cost[info_type][metric] = pd.DataFrame(metrics_df_cost[info_type][metric]).sort_index(axis=1)

        metrics_df_cost[info_type]["p_apply_A"] = pd.DataFrame(metrics_df_cost[info_type]["p_apply_A"]).sort_index(axis=1)
        metrics_df_cost[info_type]["p_apply_B"] = pd.DataFrame(metrics_df_cost[info_type]["p_apply_B"]).sort_index(axis=1)

        metrics_df_barrier[info_type]["p_apply"] = {}
        for metric in METRICS:
            metrics_df_barrier[info_type][metric] = {}
            if metric == "p_apply_":
                metrics_df_barrier[info_type]["p_apply_A"] = 1
                metrics_df_barrier[info_type]["p_apply_B"] = pd.Series({barrier: barrier for barrier in barrier_values})
                continue

            for barrier in barrier_values:
                metrics_df_barrier[info_type][metric][barrier] = {}
                for run_index in range(n_runs):
                    instance = f"{info_type}_info_barriermodel__barrierB_{format_number(barrier)}_run_{run_index}"
                    student_df = students[instance]
                    if metric == "if_gap":
                        metrics_df_barrier[info_type][metric][barrier][run_index] = (
                            student_df.query('group == "A"').groupby("skillcut_coarse")["admitted"].mean()
                            - student_df.query('group == "B"').groupby("skillcut_coarse")["admitted"].mean()
                        )
                    elif metric in METRICS_B and len(student_df.query('group == "B" and admitted == True')) == 0:
                        metrics_df_barrier[info_type][metric][barrier][run_index] = 0
                    else:
                        metrics_df_barrier[info_type][metric][barrier][run_index] = schools[instance][metric].iloc[0]
                    metrics_df_barrier[info_type]["p_apply"].setdefault(barrier, {})[run_index] = barrier

            metrics_df_barrier[info_type][metric] = pd.DataFrame(metrics_df_barrier[info_type][metric]).sort_index(axis=1)

        metrics_df_barrier[info_type]["p_apply"] = pd.DataFrame(metrics_df_barrier[info_type]["p_apply"]).sort_index(axis=1)

    matching_cost_df: dict[str, Any] = {}
    for info_type in ["high", "low"]:
        matching_cost_df[info_type] = {}
        for access_value in metrics_df_barrier[info_type]["p_apply_B"].index:
            cost_column = metrics_df_cost[info_type]["p_apply_B"].mean(axis=0)
            cost_column.index = cost_column.index.astype(float)
            absolute_diff = np.abs(access_value - cost_column)
            matching_cost_df[info_type][float(access_value)] = absolute_diff.idxmin()
        matching_cost_df[info_type] = pd.Series(matching_cost_df[info_type]).astype(float)

    matched_test_df: dict[str, dict[str, Any]] = {"high": {}, "low": {}}
    for info_type in ["high", "low"]:
        for metric in ["avgadmittedskill_A", "avgadmittedskill_B", "avgadmittedskill", "frac_B", "if_gap"]:
            matched_test_df[info_type][metric] = {
                barrier: metrics_df_cost[info_type][metric][matching_cost_df[info_type].loc[barrier]]
                for barrier in matching_cost_df[info_type].index
            }
            matched_test_df[info_type][metric] = pd.DataFrame(matched_test_df[info_type][metric])

    return {
        "metrics_df_cost": metrics_df_cost,
        "metrics_df_barrier": metrics_df_barrier,
        "matching_cost_df": matching_cost_df,
        "matched_test_df": matched_test_df,
    }


def plot_calibrated_figures(config: dict[str, Any], dry_run: bool = False) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    figure_root = resolve_repo_path(config["simulation"]["figure_output_root"])
    if dry_run:
        print(f"Would write calibrated figures under {figure_root}")
        return

    cached = read_cached_results(config)
    frames = build_metric_frames(config, cached)
    figure_root.mkdir(parents=True, exist_ok=True)

    matched_test_df = frames["matched_test_df"]
    metrics_df_barrier = frames["metrics_df_barrier"]
    drop_schools = cached["drop_schools"]
    instances = cached["instances"]

    true_skill_plot_mean = float(config["simulation"]["true_skill_plot_mean"])
    ci_width = float(config["simulation"]["ci_width"])
    access_value = float(config["simulation"]["if_gap_access_value"])

    for info_type in ["high", "low"]:
        for metric in ["frac_B", "avgadmittedskill"]:
            plt.figure()
            add_mean = true_skill_plot_mean if metric == "avgadmittedskill" else 0
            no_test_series = pd.Series(
                {
                    instance: drop_schools[info_type][instance][metric].iloc[0]
                    for instance in instances
                    if f"{info_type}_info_" in instance and instance in drop_schools[info_type]
                }
            )
            plt.axhline(
                no_test_series.mean() + add_mean,
                label="No Test",
                linestyle="dashed",
                linewidth=2,
                color="grey",
            )

            (matched_test_df[info_type][metric].mean() + add_mean).plot(label="Strategic", linewidth=2)
            se_cost = matched_test_df[info_type][metric].std() / np.sqrt(len(matched_test_df[info_type][metric]))
            plt.fill_between(
                matched_test_df[info_type][metric].columns,
                matched_test_df[info_type][metric].mean() + add_mean - se_cost * ci_width,
                matched_test_df[info_type][metric].mean() + add_mean + se_cost * ci_width,
                alpha=0.2,
            )

            (metrics_df_barrier[info_type][metric].mean() + add_mean).plot(label="Non-strategic", linewidth=2)
            se_barrier = metrics_df_barrier[info_type][metric].std() / np.sqrt(len(metrics_df_barrier[info_type][metric]))
            plt.fill_between(
                metrics_df_barrier[info_type][metric].columns,
                metrics_df_barrier[info_type][metric].mean() + add_mean - se_barrier * ci_width,
                metrics_df_barrier[info_type][metric].mean() + add_mean + se_barrier * ci_width,
                alpha=0.2,
            )

            plt.ylabel(METRIC_NAME_MAP[metric], fontsize=20)
            plt.xlabel(r"Test access level, Group $B$", fontsize=20)
            plt.legend(frameon=False, fontsize=15)
            plt.tick_params(axis="both", labelsize=15)
            plt.tight_layout()
            plt.savefig(figure_root / f"{info_type}_info_{metric}_compare_barrier_cost_notest.png", dpi=300)
            plt.close()

        metric = "if_gap"
        matched_if_gap_cost = pd.DataFrame(
            {run_index: matched_test_df[info_type][metric][access_value][run_index] for run_index in range(int(config["simulation"]["num_runs"]))}
        ).T
        matched_if_gap_barrier = pd.DataFrame(
            {run_index: metrics_df_barrier[info_type][metric][access_value][run_index] for run_index in range(int(config["simulation"]["num_runs"]))}
        ).T

        plt.figure()
        matched_if_gap_cost.mean().plot(label="Strategic", linewidth=2)
        matched_if_gap_barrier.mean().plot(label="Non-strategic", linewidth=2)

        se_cost = matched_if_gap_cost.std() / np.sqrt(len(matched_if_gap_cost))
        plt.fill_between(
            matched_if_gap_cost.columns,
            matched_if_gap_cost.mean() - se_cost * ci_width,
            matched_if_gap_cost.mean() + se_cost * ci_width,
            alpha=0.2,
        )
        se_barrier = matched_if_gap_barrier.std() / np.sqrt(len(matched_if_gap_barrier))
        plt.fill_between(
            matched_if_gap_barrier.columns,
            matched_if_gap_barrier.mean() - se_barrier * ci_width,
            matched_if_gap_barrier.mean() + se_barrier * ci_width,
            alpha=0.2,
        )

        plt.axhline(0, linestyle="dashed", color="grey")
        plt.ylabel(METRIC_NAME_MAP[metric], fontsize=20)
        plt.xlabel(r"Test access level, Group $B$", fontsize=20)
        plt.legend(frameon=False, fontsize=15)
        plt.tick_params(axis="both", labelsize=15)
        plt.tight_layout()
        plt.savefig(figure_root / f"{info_type}_info_{metric}_compare_barrier_cost_notest.png", dpi=300)
        plt.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true", help="Print planned work without running simulations or plotting.")
    parser.add_argument("--plots-only", action="store_true", help="Only aggregate and plot from the configured cache.")
    parser.add_argument("--simulations-only", action="store_true", help="Only run missing simulations; do not make plots.")
    parser.add_argument("--cache-root", type=Path, help="Override simulation.output_root from the config.")
    parser.add_argument("--output-dir", type=Path, help="Override simulation.figure_output_root from the config.")
    parser.add_argument("--overwrite", action="store_true", help="Rerun simulation directories that already exist.")
    args = parser.parse_args(argv)

    if args.plots_only and args.simulations_only:
        print("--plots-only and --simulations-only cannot both be set.", file=sys.stderr)
        return 2

    config_path = resolve_repo_path(args.config)
    config = load_config(config_path)
    if args.cache_root is not None:
        config["simulation"]["output_root"] = str(args.cache_root)
    if args.output_dir is not None:
        config["simulation"]["figure_output_root"] = str(args.output_dir)
    validate_config(config)

    if not args.plots_only:
        run_simulations(config, overwrite=args.overwrite, dry_run=args.dry_run)
    if not args.simulations_only:
        plot_calibrated_figures(config, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
