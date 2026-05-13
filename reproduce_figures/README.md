# Figure reproduction

This folder contains the code-only reproduction wrapper for the paper figures in
arXiv:2010.04396. Generated figures, staged caches, and large migrated CSV
inputs are intentionally not part of the code commit.

Run the ordered figure pipeline from the repository root:

```bash
python reproduce_figures/scripts/reproduce_all_figures.py --cores 32
```

For a cache-first server run that avoids force-rerunning the very heavy
two-school Figure 6/14 simulations, do not pass `--rerun-simulations`:

```bash
REPRO_CORES=32 python reproduce_figures/scripts/reproduce_arxiv_2010_04396_figures.py \
  --cores 32 \
  --allow-heavy \
  --generated-root reproduce_figures/workspace/server_cache_first/generated \
  --cache-root reproduce_figures/workspace/server_cache_first/cache \
  --output-root reproduce_figures/outputs/arxiv_2010_04396_server_cache_first
```

For a cache-only/local smoke run, use `--skip-generators` and explicit local
roots, for example:

```bash
python reproduce_figures/scripts/reproduce_arxiv_2010_04396_figures.py \
  --cores 4 \
  --allow-heavy \
  --skip-generators \
  --generated-root reproduce_figures/workspace/cache_only_4cores/generated \
  --cache-root reproduce_figures/workspace/cache_only_4cores/cache \
  --output-root reproduce_figures/outputs/arxiv_2010_04396_cache_only_4cores
```

Current cache-backed status:

- Reproduced: Figures 1, 2, 3, 4, 5, 6, 9, 10, 14, and 15b.
- Still data/heavy blocked: Figures 7, 8, 11, 12, 13, and 15a.

Layout:

- `scripts/`: runnable wrappers and figure-specific replot/rerun entrypoints.
- `legacy_code/`: minimal legacy plotting helpers needed by the wrappers.
- `inputs/`: expected location for migrated compact inputs and fit parameters.
- `workspace/`: generated intermediates and staged caches, ignored locally.
- `outputs/`: flat copied figure bundle, ignored locally.
