#!/usr/bin/env python3
"""One-command full rerun entrypoint for the arXiv:2010.04396 paper figures."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REPRO_ROOT = REPO_ROOT / "reproduce_figures"
DEFAULT_WORKSPACE_ROOT = REPRO_ROOT / "workspace"
DEFAULT_OUTPUT_ROOT = REPRO_ROOT / "outputs" / "arxiv_2010_04396_rerun"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=DEFAULT_WORKSPACE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--cores", type=int, default=int(os.environ.get("REPRO_CORES", "1")))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--skip-generators",
        action="store_true",
        help="Do not run plotting or simulation generators; only bundle artifacts that already exist under the workspace/generated root.",
    )
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
        str(REPRO_ROOT / "scripts" / "reproduce_arxiv_2010_04396_figures.py"),
        "--cores",
        str(args.cores),
        "--generated-root",
        str(args.workspace_root / "generated"),
        "--cache-root",
        str(args.workspace_root / "cache"),
        "--output-root",
        str(args.output_root),
    ]
    if not args.skip_generators:
        command.extend(["--allow-heavy", "--rerun-simulations"])
    if args.dry_run:
        command.append("--dry-run")
    if args.skip_generators:
        command.append("--skip-generators")
    completed = subprocess.run(command, cwd=REPO_ROOT, env=command_env())
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
