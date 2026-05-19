# Figure reproduction

This folder contains the wrapper code needed to regenerate the paper figures. Generated figures, intermediate workspaces, and local simulation caches are intentionally ignored.

## Reproduce from an existing local cache

Run from the repository root:

```bash
python reproduce_figures/scripts/reproduce_all_figures.py --cores 4
```

By default this reads the local combined cache at:

```text
reproduce_figures/example_simulation_cache
```

and writes the flat figure bundle to:

```text
reproduce_figures/outputs/paper_figures
```

The cache, workspace, and output folders are ignored by git.

## Ignored cache layout

The ignored local example cache combines the simulation outputs needed by the plotting wrappers:

- `mult_schools_simulations_policy_testing/`: two-school strategic heatmaps.
- `cost_model_single_school/`: strategic single-school apply-by-skill panel.
- `calibrated_theop_mult_runs/`: calibrated THEOP synthetic-student simulations.
- `cost_model_single_school_fix_A1_equal_B1/`: strategic single-school cost and variance sweep.
- `cost_model_single_school_cost_sweep/`: strategic cost-sweep metrics.
- `cost_model_single_school_drop_test_heatmaps/`: drop-test heatmap metrics.
- `legacy_nonstrategic/`: migrated legacy nonstrategic and unaware/AA caches.

## One-command from-scratch regeneration

To rebuild the ignored example cache and final plots on a server, run from the repository root:

```bash
CORES=32 ./reproduce_figures/reproduce_paper_figures.sh
```

The shell script writes regenerated cache files into ignored `reproduce_figures/example_simulation_cache`, generated intermediates under ignored `reproduce_figures/workspace/generated`, and the final bundle under ignored `reproduce_figures/outputs/paper_figures`.

Useful override for a custom Python environment:

```bash
PYTHON=/path/to/python CORES=32 ./reproduce_figures/reproduce_paper_figures.sh
```

## Layout

- `scripts/`: runnable wrappers and figure-specific replot/rerun entrypoints.
- `legacy_code/`: minimal legacy plotting helpers needed by the wrappers.
- `paper_sources/`: TeX snippets for the two paper-native figures.
- `example_simulation_cache/`: ignored local combined cache used by the one-command reproduction path.
- `workspace/`: ignored generated intermediates.
- `outputs/`: ignored flat figure bundles.
