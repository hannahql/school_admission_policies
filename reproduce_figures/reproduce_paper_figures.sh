#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
CORES="${CORES:-${REPRO_CORES:-4}}"
CACHE_ROOT="${CACHE_ROOT:-reproduce_figures/example_simulation_cache}"
GENERATED_ROOT="${GENERATED_ROOT:-reproduce_figures/workspace/generated}"
OUTPUT_ROOT="${OUTPUT_ROOT:-reproduce_figures/outputs/paper_figures}"

export PYTHONNOUSERSITE="${PYTHONNOUSERSITE:-1}"
export TMPDIR="${LOCAL_TMPDIR:-${TMPDIR:-/tmp}}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib_ms_figs}"

mkdir -p "$CACHE_ROOT" "$GENERATED_ROOT" "$OUTPUT_ROOT" "$MPLCONFIGDIR"

echo "Python: $PYTHON"
echo "Cores: $CORES"
echo "Cache root: $CACHE_ROOT"
echo "Generated root: $GENERATED_ROOT"
echo "Output root: $OUTPUT_ROOT"

"$PYTHON" reproduce_figures/scripts/reproduce_all_figures.py \
  --cores "$CORES" \
  --rerun-simulations \
  --generated-root "$GENERATED_ROOT" \
  --cache-root "$CACHE_ROOT" \
  --output-root "$OUTPUT_ROOT"
