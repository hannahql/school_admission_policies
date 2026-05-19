#!/usr/bin/env python3
"""One-command cache-first entrypoint for the paper figures."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REPRO_ROOT = REPO_ROOT / "reproduce_figures"
DEFAULT_GENERATED_ROOT = REPRO_ROOT / "workspace" / "generated"
DEFAULT_CACHE_ROOT = REPRO_ROOT / "example_simulation_cache"
DEFAULT_OUTPUT_ROOT = REPRO_ROOT / "outputs" / "paper_figures"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-root", type=Path, default=DEFAULT_GENERATED_ROOT)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--cores", type=int, default=int(os.environ.get("REPRO_CORES", "1")))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rerun-simulations", action="store_true", help="Regenerate missing/heavy caches instead of requiring the example cache.")
    parser.add_argument("--skip-generators", action="store_true", help="Only bundle files that already exist under --generated-root.")
    return parser.parse_args()


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    env.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ms_figs")
    return env


def main() -> int:
    args = parse_args()
    command = [
        sys.executable,
        str(REPRO_ROOT / "scripts" / "reproduce_paper_figures.py"),
        "--cores",
        str(args.cores),
        "--allow-heavy",
        "--generated-root",
        str(args.generated_root),
        "--cache-root",
        str(args.cache_root),
        "--output-root",
        str(args.output_root),
    ]
    if args.rerun_simulations:
        command.append("--rerun-simulations")
    if args.dry_run:
        command.append("--dry-run")
    if args.skip_generators:
        command.append("--skip-generators")
    completed = subprocess.run(command, cwd=REPO_ROOT, env=command_env())
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
