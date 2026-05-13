#!/usr/bin/env python3
"""Create an ordered reproduction bundle for arXiv:2010.04396 figures.

The bundle is organized in PDF figure order. This script only edits/copies
outputs under the requested output directory. It does not modify simulation
modules or notebooks.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REPRO_ROOT = REPO_ROOT / "reproduce_figures"
PAPER_ROOT = REPRO_ROOT / "paper_sources" / "arxiv_2010_04396"
DEFAULT_OUTPUT_ROOT = REPRO_ROOT / "outputs" / "arxiv_2010_04396"
DEFAULT_GENERATED_ROOT = REPRO_ROOT / "workspace" / "generated"
DEFAULT_CACHE_ROOT = REPRO_ROOT / "workspace" / "cache"
REPRODUCTION_INPUTS = REPRO_ROOT / "inputs"


@dataclass(frozen=True)
class Panel:
    source: str
    output: str
    kind: str = "artifact"


@dataclass(frozen=True)
class Figure:
    number: int
    slug: str
    status: str
    panels: tuple[Panel, ...]
    generator: tuple[str, ...] = ()
    rerun_generator: tuple[str, ...] = ()
    note: str = ""


FIGURES: tuple[Figure, ...] = (
    Figure(
        1,
        "normals_intuition",
        "tex_native",
        (Panel("intuition.tex:8:40", "figure_source.tex", "tex_range"),),
        note="TikZ-native figure in the paper source.",
    ),
    Figure(
        2,
        "skill_vs_estimate_joint_distributions",
        "implemented_heavy",
        (
            Panel("plots/simulations_2d_skillestimates_nobudget_2dskilldist_testbased.pdf", "a_nobudget_testbased.pdf"),
            Panel("plots/simulations_2d_skillestimates_barrier_2dskilldist_testbased.pdf", "b_barrier_testbased.pdf"),
            Panel("plots/simulations_2d_skillestimates_barrier_2dskilldist_testfree.pdf", "c_barrier_testfree.pdf"),
        ),
        generator=("reproduce_figures/scripts/replot_legacy_intuition_from_2020.py",),
        rerun_generator=("reproduce_figures/scripts/replot_legacy_intuition_from_2020.py",),
        note="Small rerun wrapper: two 2020 SINGLE_SCHOOL simulations generate the three joint-distribution panels. Runs only with --allow-heavy.",
    ),
    Figure(
        3,
        "variance_and_access_six_panel",
        "generated_from_legacy_cache",
        (
            Panel("plots/simulations_vary_feature1_var_update_avgadmittedskill.pdf", "a_variance_avgadmittedskill.pdf"),
            Panel("plots/simulations_vary_feature1_var_update_frac.pdf", "b_variance_frac.pdf"),
            Panel("plots/simulations_vary_feature1_var_update_2dIF_FEATURE_DIST_B1_var.pdf", "c_variance_if.pdf"),
            Panel("plots/simulations_vary_barrier_avgadmittedskill_PROB_MEETS_BUDGET_B.pdf", "d_barrier_avgadmittedskill.pdf"),
            Panel("plots/simulations_vary_barrier_frac_PROB_MEETS_BUDGET_B.pdf", "e_barrier_frac.pdf"),
            Panel("plots/simulations_vary_barrier_2dIF_PROB_MEETS_BUDGET_B.pdf", "f_barrier_if.pdf"),
        ),
        generator=("reproduce_figures/scripts/replot_legacy_nonstrategic_from_2020.py", "--figure-set", "variance_and_barrier"),
        rerun_generator=("reproduce_figures/scripts/rerun_legacy_nonstrategic_cache_from_2020.py", "--figure-set", "variance_and_barrier", "--force-rerun"),
    ),
    Figure(
        4,
        "individual_fairness_no_affirmative_action",
        "generated_from_legacy_cache",
        (Panel("plots/paper_budgetsimulations_forstudentIF_update4_indivfairness_withunaware_noAA.pdf", "individual_fairness_withunaware_noAA.pdf"),),
        generator=("reproduce_figures/scripts/replot_legacy_nonstrategic_from_2020.py", "--figure-set", "fairness"),
        rerun_generator=("reproduce_figures/scripts/rerun_legacy_nonstrategic_cache_from_2020.py", "--figure-set", "fairness", "--force-rerun"),
    ),
    Figure(
        5,
        "two_school_student_regions",
        "tex_native",
        (Panel("strategic_new_nov_edit.tex:178:257", "figure_source.tex", "tex_range"),),
        note="TikZ-native figure in the paper source.",
    ),
    Figure(
        6,
        "two_school_heatmaps_low_high_cost",
        "generated_from_20260323_cache",
        (
            Panel("second_round_MS/figures_ms_2025_dec_revision/avg_skill_heatmap_STUDENT_TEST_COST=0.5_UTILITY_a=3_UTILITY_b=2_sems.png", "a_cost_0.5.png"),
            Panel("second_round_MS/figures_ms_2025_dec_revision/avg_skill_heatmap_STUDENT_TEST_COST=2.0_UTILITY_a=3_UTILITY_b=2_sems.png", "b_cost_2.0.png"),
        ),
        generator=("reproduce_figures/scripts/replot_strategic_two_school_from_cache.py",),
        rerun_generator=("reproduce_figures/scripts/rerun_strategic_two_school_heatmaps.py", "--force-rerun"),
        note="Replots from simulation_data/20260323.",
    ),
    Figure(
        7,
        "calibrated_high_info",
        "implemented_heavy",
        (
            Panel("plots_may_2025_calibration_updates/high_info_avgadmittedskill_compare_barrier_cost_notest.png", "a_avgadmittedskill.png"),
            Panel("plots_may_2025_calibration_updates/high_info_frac_B_compare_barrier_cost_notest.png", "b_frac_B.png"),
            Panel("plots_may_2025_calibration_updates/high_info_if_gap_compare_barrier_cost_notest.png", "c_if_gap.png"),
        ),
        generator=("reproduce_figures/scripts/replot_calibrated_theop_from_fit_params.py",),
        rerun_generator=("reproduce_figures/scripts/replot_calibrated_theop_from_fit_params.py",),
        note="Runs a large synthetic-simulation grid only with --allow-heavy.",
    ),
    Figure(
        8,
        "calibrated_low_info",
        "implemented_heavy",
        (
            Panel("plots_may_2025_calibration_updates/low_info_avgadmittedskill_compare_barrier_cost_notest.png", "a_avgadmittedskill.png"),
            Panel("plots_may_2025_calibration_updates/low_info_frac_B_compare_barrier_cost_notest.png", "b_frac_B.png"),
            Panel("plots_may_2025_calibration_updates/low_info_if_gap_compare_barrier_cost_notest.png", "c_if_gap.png"),
        ),
        generator=("reproduce_figures/scripts/replot_calibrated_theop_from_fit_params.py",),
        rerun_generator=("reproduce_figures/scripts/replot_calibrated_theop_from_fit_params.py",),
        note="Runs a large synthetic-simulation grid only with --allow-heavy.",
    ),
    Figure(
        9,
        "non_strategic_2d_policy_differences",
        "generated_from_legacy_cache",
        (
            Panel("plots/simulations_vary_feature1_and_disbudget_2ddifference_avgadmittedskill.pdf", "a_avgadmittedskill.pdf"),
            Panel("plots/simulations_vary_feature1_and_disbudget_2ddifference_frac_B.pdf", "b_frac_B.pdf"),
            Panel("plots/simulations_vary_feature1_and_disbudget_2ddifference_avgadmittedskill_A.pdf", "c_avgadmittedskill_A.pdf"),
            Panel("plots/simulations_vary_feature1_and_disbudget_2ddifference_avgadmittedskill_B.pdf", "d_avgadmittedskill_B.pdf"),
        ),
        generator=("reproduce_figures/scripts/replot_legacy_nonstrategic_from_2020.py", "--figure-set", "two_dimensional_differences"),
        rerun_generator=("reproduce_figures/scripts/rerun_legacy_nonstrategic_cache_from_2020.py", "--figure-set", "two_dimensional_differences", "--force-rerun"),
    ),
    Figure(
        10,
        "strategic_apply_by_skill",
        "generated_from_single_school_cache",
        (Panel("second_round_MS/figures_ms_2025_revision/p_apply_by_skill_group.png", "p_apply_by_skill_group.png"),),
        generator=("reproduce_figures/scripts/replot_strategic_single_school_from_cache.py", "--figure-set", "ec4_apply_by_skill"),
        rerun_generator=("reproduce_figures/scripts/rerun_strategic_single_school_ec4.py", "--force-rerun"),
        note="Replots from simulation_data/cost_model_single_school.",
    ),
    Figure(
        11,
        "strategic_cost_and_feature_variance",
        "implemented_heavy",
        (
            Panel("second_round_MS/figures_ms_2025_revision/avgadmittedskill_strategic.png", "a_avgadmittedskill.png"),
            Panel("second_round_MS/figures_ms_2025_revision/frac_A_strategic.png", "b_frac_A.png"),
            Panel("second_round_MS/figures_ms_2025_revision/IF_strategic.png", "c_IF.png"),
        ),
        generator=("reproduce_figures/scripts/replot_strategic_single_school_sweep_heavy.py",),
        rerun_generator=("reproduce_figures/scripts/replot_strategic_single_school_sweep_heavy.py", "--force-rerun"),
        note="Heavy cache-first wrapper reruns the traced fix_A1_equal_B1 cost sweep only with --allow-heavy.",
    ),
    Figure(
        12,
        "strategic_cost_sweep",
        "implemented_heavy",
        (
            Panel("plots_ms_revision/costA_0.5/p_apply.png", "a_p_apply.png"),
            Panel("plots_ms_revision/costA_0.5/avg_admitted_skill.png", "b_avg_admitted_skill.png"),
            Panel("plots_ms_revision/costA_0.5/frac_B_cost.png", "c_frac_B_cost.png"),
        ),
        generator=("reproduce_figures/scripts/replot_strategic_cost_sweep_heavy.py",),
        rerun_generator=("reproduce_figures/scripts/replot_strategic_cost_sweep_heavy.py", "--force-rerun"),
        note="Heavy cache-first wrapper reconstructs the final-paper strategic cost sweep. Runs only with --allow-heavy.",
    ),
    Figure(
        13,
        "strategic_drop_test_heatmaps",
        "implemented_heavy",
        (
            Panel("plots_ms_revision/costA_0.5_old/drop_test_diversity_level_vary_costB_varB_heatmap.png", "a_drop_test_diversity.png"),
            Panel("plots_ms_revision/costA_0.5_old/drop_test_academic_merit_vary_costB_varB_heatmap.png", "b_drop_test_academic_merit.png"),
        ),
        generator=("reproduce_figures/scripts/replot_strategic_drop_test_heatmaps_heavy.py",),
        rerun_generator=("reproduce_figures/scripts/replot_strategic_drop_test_heatmaps_heavy.py", "--force-rerun"),
        note="Heavy cache-first wrapper reconstructs the drop-test heatmaps from strategic cost-model simulations. Runs only with --allow-heavy.",
    ),
    Figure(
        14,
        "two_school_heatmap_mid_cost",
        "generated_from_20260323_cache",
        (Panel("second_round_MS/figures_ms_2025_dec_revision/avg_skill_heatmap_STUDENT_TEST_COST=1.5_UTILITY_a=3_UTILITY_b=2_sems.png", "avg_skill_heatmap_cost_1.5.png"),),
        generator=("reproduce_figures/scripts/replot_strategic_two_school_from_cache.py",),
        rerun_generator=("reproduce_figures/scripts/rerun_strategic_two_school_heatmaps.py", "--force-rerun"),
        note="Replots from simulation_data/20260323.",
    ),
    Figure(
        15,
        "affirmative_action_and_unaware",
        "implemented_heavy",
        (
            Panel("plots/paper_simulationsbudget_pareto_update2_differentpoliciescurves_withunaware.pdf", "a_pareto_withunaware.pdf"),
            Panel("plots/paper_budgetsimulations_forstudentIF_update4_indivfairness_withunaware.pdf", "b_individual_fairness_withunaware.pdf"),
        ),
        generator=("reproduce_figures/scripts/replot_legacy_unaware_aa_heavy_from_2020.py",),
        rerun_generator=("reproduce_figures/scripts/replot_legacy_unaware_aa_heavy_from_2020.py", "--force-rerun"),
        note="Heavy cache-first wrapper reruns the missing Pareto metrics from the traced 2020 grid and regenerates the IF panel from paperclean5 cache. Runs only with --allow-heavy.",
    ),
)

GENERATED_STATUSES = {
    "generated_from_legacy_cache",
    "generated_from_20260323_cache",
    "generated_from_single_school_cache",
    "implemented_heavy",
    "tex_native",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--generated-root", type=Path, default=DEFAULT_GENERATED_ROOT)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--paper-root", type=Path, default=PAPER_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-generators", action="store_true")
    parser.add_argument("--allow-heavy", action="store_true", help="Allow heavy synthetic simulation generators, including calibrated THEOP.")
    parser.add_argument("--rerun-simulations", action="store_true", help="Use force-rerun generator variants where available.")
    parser.add_argument("--cores", type=int, default=int(os.environ.get("REPRO_CORES", "1")), help="Cores to pass to rerun generators that support parallelism.")
    return parser.parse_args()


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    env.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")
    return env


def option_value(command: list[str], option: str) -> str | None:
    try:
        return command[command.index(option) + 1]
    except (ValueError, IndexError):
        return None


def append_option(command: list[str], option: str, value: Path | str | int | float) -> list[str]:
    if option in command:
        return command
    return [*command, option, str(value)]


def append_flag(command: list[str], option: str) -> list[str]:
    if option in command:
        return command
    return [*command, option]


def generated_output_dir(figure: Figure, args: argparse.Namespace) -> Path | None:
    parents = {Path(panel.source).parent for panel in figure.panels if panel.kind != "tex_range"}
    if not parents:
        return None
    if len(parents) != 1:
        raise ValueError(f"Figure {figure.number} has panels under multiple generated roots: {sorted(str(parent) for parent in parents)}")
    return args.generated_root / next(iter(parents))


def legacy_nonstrategic_cache_dir(generator: tuple[str, ...], args: argparse.Namespace) -> Path:
    figure_set = option_value(list(generator), "--figure-set") or "all"
    return args.cache_root / "legacy_nonstrategic" / figure_set


def copy_missing_tree(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copy2(source, destination)
        return
    destination.mkdir(parents=True, exist_ok=True)
    for source_path in source.rglob("*"):
        destination_path = destination / source_path.relative_to(source)
        if source_path.is_dir():
            destination_path.mkdir(parents=True, exist_ok=True)
        elif not destination_path.exists():
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)


def stage_existing_cache(source: Path, destination: Path, args: argparse.Namespace) -> None:
    if args.rerun_simulations:
        return
    copy_missing_tree(source, destination)


TWO_SCHOOL_POLICIES = ("FULL_FULL_test", "FULL_SUB_test", "SUB_FULL_test", "SUB_SUB_test")
TWO_SCHOOL_REQUIRED_GLOBS = ("parameters_of_interest_*.json", "schools_df_*.csv")


def required_two_school_files(policy_dir: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in TWO_SCHOOL_REQUIRED_GLOBS:
        files.extend(sorted(policy_dir.glob(pattern)))
    return files


def staged_cache_is_complete(source: Path, destination: Path) -> bool:
    if not destination.exists():
        return False
    for policy in TWO_SCHOOL_POLICIES:
        source_policy = source / policy
        destination_policy = destination / policy
        if not destination_policy.is_dir():
            return False
        source_files = required_two_school_files(source_policy)
        if not source_files:
            return False
        if any(not (destination_policy / source_file.name).is_file() for source_file in source_files):
            return False
    return True


def unavailable_two_school_files(source: Path, destination: Path) -> list[Path]:
    unavailable: list[Path] = []
    for policy in TWO_SCHOOL_POLICIES:
        source_policy = source / policy
        destination_policy = destination / policy
        for source_file in required_two_school_files(source_policy):
            if (destination_policy / source_file.name).is_file():
                continue
            try:
                stat_result = source_file.stat()
            except OSError:
                unavailable.append(source_file)
                continue
            if source_file.suffix == ".csv" and stat_result.st_size > 0 and stat_result.st_blocks == 0:
                unavailable.append(source_file)
    return unavailable


def populate_staged_two_school_cache(source: Path, destination: Path) -> None:
    unavailable = unavailable_two_school_files(source, destination)
    if unavailable:
        preview = ", ".join(str(path.relative_to(source)) for path in unavailable[:5])
        raise OSError(
            "Cannot stage two-school cache because required CSV files look like "
            f"OneDrive cloud placeholders from WSL: {preview}"
        )
    if destination.exists():
        shutil.rmtree(destination)
    for policy in TWO_SCHOOL_POLICIES:
        source_policy = source / policy
        destination_policy = destination / policy
        destination_policy.mkdir(parents=True, exist_ok=True)
        for source_file in required_two_school_files(source_policy):
            try:
                shutil.copy2(source_file, destination_policy / source_file.name)
            except OSError as exc:
                raise OSError(f"Could not stage required two-school cache file: {source_file}") from exc


def staged_two_school_cache(args: argparse.Namespace) -> Path:
    source = REPO_ROOT / "simulation_data" / "20260323"
    if args.dry_run:
        return source
    destination = Path("/tmp") / "ms_figs_20260323_cache"
    if not staged_cache_is_complete(source, destination):
        populate_staged_two_school_cache(source, destination)
    return destination


def command_with_runner_options(command: list[str], generator: tuple[str, ...], figure: Figure, args: argparse.Namespace) -> list[str]:
    script = generator[0]
    output_dir = generated_output_dir(figure, args)
    if output_dir is not None and script in {
        "reproduce_figures/scripts/replot_legacy_intuition_from_2020.py",
        "reproduce_figures/scripts/rerun_legacy_nonstrategic_cache_from_2020.py",
        "reproduce_figures/scripts/replot_legacy_nonstrategic_from_2020.py",
        "reproduce_figures/scripts/replot_calibrated_theop_from_fit_params.py",
        "reproduce_figures/scripts/replot_strategic_two_school_from_cache.py",
        "reproduce_figures/scripts/rerun_strategic_two_school_heatmaps.py",
        "reproduce_figures/scripts/rerun_strategic_single_school_ec4.py",
        "reproduce_figures/scripts/replot_strategic_single_school_from_cache.py",
        "reproduce_figures/scripts/replot_strategic_single_school_sweep_heavy.py",
        "reproduce_figures/scripts/replot_strategic_cost_sweep_heavy.py",
        "reproduce_figures/scripts/replot_strategic_drop_test_heatmaps_heavy.py",
        "reproduce_figures/scripts/replot_legacy_unaware_aa_heavy_from_2020.py",
    }:
        command = append_option(command, "--output-dir", output_dir)

    if script == "reproduce_figures/scripts/replot_legacy_nonstrategic_from_2020.py":
        cache_dir = legacy_nonstrategic_cache_dir(generator, args)
        stage_existing_cache(REPRODUCTION_INPUTS, cache_dir, args)
        command = append_option(command, "--cache-dir", cache_dir)
    elif script == "reproduce_figures/scripts/replot_calibrated_theop_from_fit_params.py":
        cache_root = args.cache_root / "calibrated_theop_from_fit_params"
        stage_existing_cache(REPO_ROOT / "simulation_data" / "calibrated_theop_from_fit_params", cache_root, args)
        command = append_option(command, "--cache-root", cache_root)
    elif script == "reproduce_figures/scripts/replot_strategic_single_school_from_cache.py":
        cache_root = args.cache_root / "cost_model_single_school"
        stage_existing_cache(REPO_ROOT / "simulation_data" / "cost_model_single_school", cache_root, args)
        command = append_option(command, "--cache-root", cache_root)
    elif script == "reproduce_figures/scripts/replot_strategic_single_school_sweep_heavy.py":
        cache_root = args.cache_root / "cost_model_single_school_fix_A1_equal_B1"
        stage_existing_cache(REPO_ROOT / "simulation_data" / "cost_model_single_school_fix_A1_equal_B1", cache_root, args)
        command = append_option(command, "--cache-root", cache_root)
    elif script == "reproduce_figures/scripts/replot_strategic_cost_sweep_heavy.py":
        cache_root = args.cache_root / "cost_model_single_school_cost_sweep"
        stage_existing_cache(REPO_ROOT / "simulation_data" / "cost_model_single_school_cost_sweep", cache_root, args)
        command = append_option(command, "--cache-root", cache_root)
    elif script == "reproduce_figures/scripts/replot_strategic_drop_test_heatmaps_heavy.py":
        cache_root = args.cache_root / "cost_model_single_school_drop_test_heatmaps"
        stage_existing_cache(REPO_ROOT / "simulation_data" / "cost_model_single_school_drop_test_heatmaps", cache_root, args)
        command = append_option(command, "--cache-root", cache_root)
    elif script == "reproduce_figures/scripts/replot_legacy_unaware_aa_heavy_from_2020.py":
        pareto_cache_dir = args.cache_root / "legacy_nonstrategic" / "generated_pareto"
        if_cache_dir = args.cache_root / "legacy_nonstrategic" / "fairness"
        stage_existing_cache(REPRODUCTION_INPUTS, pareto_cache_dir, args)
        stage_existing_cache(REPRODUCTION_INPUTS, if_cache_dir, args)
        command = append_option(command, "--cache-dir", pareto_cache_dir)
        command = append_option(command, "--if-cache-dir", if_cache_dir)

    if args.rerun_simulations:
        if script == "reproduce_figures/scripts/rerun_legacy_nonstrategic_cache_from_2020.py":
            command = append_option(command, "--cache-dir", legacy_nonstrategic_cache_dir(generator, args))
        elif script == "reproduce_figures/scripts/replot_calibrated_theop_from_fit_params.py":
            command = append_option(command, "--cache-root", args.cache_root / "calibrated_theop_from_fit_params")
        elif script == "reproduce_figures/scripts/rerun_strategic_single_school_ec4.py":
            command = append_option(command, "--cache-root", args.cache_root / "cost_model_single_school_ec4")
        elif script == "reproduce_figures/scripts/replot_strategic_single_school_sweep_heavy.py":
            command = append_option(command, "--cache-root", args.cache_root / "cost_model_single_school_fix_A1_equal_B1")
        elif script == "reproduce_figures/scripts/replot_strategic_cost_sweep_heavy.py":
            command = append_option(command, "--cache-root", args.cache_root / "cost_model_single_school_cost_sweep")
        elif script == "reproduce_figures/scripts/replot_strategic_drop_test_heatmaps_heavy.py":
            command = append_option(command, "--cache-root", args.cache_root / "cost_model_single_school_drop_test_heatmaps")
        elif script == "reproduce_figures/scripts/rerun_strategic_two_school_heatmaps.py":
            command = append_option(command, "--cache-root", args.cache_root / "20260323_rerun")
        elif script == "reproduce_figures/scripts/replot_legacy_unaware_aa_heavy_from_2020.py":
            command = append_option(command, "--cache-dir", args.cache_root / "legacy_unaware_aa_pareto")
            command = append_option(command, "--if-cache-dir", args.cache_root / "legacy_nonstrategic" / "fairness")
    else:
        if script == "reproduce_figures/scripts/replot_calibrated_theop_from_fit_params.py":
            command = append_flag(command, "--plots-only")
        elif script == "reproduce_figures/scripts/replot_strategic_two_school_from_cache.py":
            command = append_option(command, "--cache-root", staged_two_school_cache(args))
        elif script in {
            "reproduce_figures/scripts/replot_strategic_single_school_sweep_heavy.py",
            "reproduce_figures/scripts/replot_strategic_cost_sweep_heavy.py",
            "reproduce_figures/scripts/replot_strategic_drop_test_heatmaps_heavy.py",
            "reproduce_figures/scripts/replot_legacy_unaware_aa_heavy_from_2020.py",
        }:
            command = append_flag(command, "--no-rerun-missing")

    if script in {
        "reproduce_figures/scripts/rerun_legacy_nonstrategic_cache_from_2020.py",
        "reproduce_figures/scripts/rerun_strategic_two_school_heatmaps.py",
    }:
        command = append_option(command, "--n-processes", args.cores)
    return command


def run_generator(figure: Figure, args: argparse.Namespace) -> str:
    if figure.status not in GENERATED_STATUSES:
        return "blocked"
    generator = figure.generator
    using_rerun = args.rerun_simulations and bool(figure.rerun_generator)
    if using_rerun:
        generator = figure.rerun_generator
    if not generator:
        return "not_applicable"
    if args.skip_generators:
        return "skipped_by_request"
    if (figure.status == "implemented_heavy" or using_rerun) and not args.allow_heavy:
        return "skipped_heavy"

    command = [sys.executable, str(REPO_ROOT / generator[0]), *generator[1:]]
    try:
        command = command_with_runner_options(command, generator, figure, args)
    except Exception as exc:
        return f"failed_setup_{type(exc).__name__}: {exc}"
    if args.dry_run:
        return "dry_run: " + " ".join(command)
    completed = subprocess.run(command, cwd=REPO_ROOT, env=command_env())
    return "ok" if completed.returncode == 0 else f"failed_exit_{completed.returncode}"


def source_candidates(panel: Panel, args: argparse.Namespace) -> list[Path]:
    rel = Path(panel.source)
    return [args.generated_root / rel, REPO_ROOT / rel]


def copy_generated_output(panel: Panel, destination: Path, args: argparse.Namespace) -> tuple[str, str]:
    for source in source_candidates(panel, args):
        if source.exists():
            if not args.dry_run:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            return "ok", str(source)
    return "missing", panel.source


def extract_tex_range(panel: Panel, destination: Path, args: argparse.Namespace) -> tuple[str, str]:
    path_text, start_text, end_text = panel.source.split(":")
    source = args.paper_root / path_text
    start = int(start_text)
    end = int(end_text)
    if not source.exists():
        return "missing", str(source)
    if args.dry_run:
        return "dry_run", str(source)

    lines = source.read_text(encoding="utf-8").splitlines()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines[start - 1 : end]) + "\n", encoding="utf-8")
    return "ok", f"{source}:{start}-{end}"


def handle_panel(figure: Figure, panel: Panel, destination: Path, args: argparse.Namespace, generator_status: str) -> tuple[str, str]:
    if panel.kind == "tex_range":
        return extract_tex_range(panel, destination, args)
    if figure.status not in GENERATED_STATUSES:
        return "blocked_no_generator", panel.source
    if generator_status == "skipped_by_request" and args.skip_generators:
        return copy_generated_output(panel, destination, args)
    if generator_status != "ok" and not generator_status.startswith("dry_run:"):
        return f"blocked_generator_{generator_status}", panel.source
    return copy_generated_output(panel, destination, args)


def flat_panel_output_name(figure: Figure, panel: Panel) -> str:
    path = Path(panel.output)
    suffix = path.suffix or ".tex"
    stem = path.stem
    if len(stem) > 2 and stem[1] == "_" and stem[0] in "abcdef":
        return f"figure_{figure.number:02d}{stem[0]}_{stem[2:]}{suffix}"
    return f"figure_{figure.number:02d}_{stem}{suffix}"


def write_status(rows: list[dict[str, str]], output_root: Path, dry_run: bool) -> None:
    if dry_run:
        return
    output_root.mkdir(parents=True, exist_ok=True)
    lines = [
        "# arXiv 2010.04396 figure reproduction status",
        "",
        "| Figure | Bundle status | Generator | Panel | Panel status | Source |",
        "|---:|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['figure']} | {row['bundle_status']} | {row['generator_status']} | "
            f"{row['panel']} | {row['panel_status']} | `{row['source']}` |"
        )
    (output_root / "REPRODUCTION_STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows: list[dict[str, str]] = []

    for figure in FIGURES:
        generator_status = run_generator(figure, args)

        for panel in figure.panels:
            output_name = flat_panel_output_name(figure, panel)
            panel_status, source_used = handle_panel(figure, panel, args.output_root / output_name, args, generator_status)
            rows.append(
                {
                    "figure": str(figure.number),
                    "bundle_status": figure.status,
                    "generator_status": generator_status,
                    "panel": output_name,
                    "panel_status": panel_status,
                    "source": source_used,
                }
            )

    write_status(rows, args.output_root, args.dry_run)
    for row in rows:
        print(
            f"Figure {row['figure']:>2} {row['panel_status']:<8} "
            f"{row['panel']} <- {row['source']}"
        )
    return 0 if all(row["panel_status"] in {"ok", "dry_run"} for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
