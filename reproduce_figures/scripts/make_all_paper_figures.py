#!/usr/bin/env python3
"""Run manifest-listed paper figure generators.

By default this only runs families marked status: implemented. Use --status to
opt into other statuses after their generators and caches are ready.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

from check_paper_figure_inputs import (
    DEFAULT_MANIFEST,
    generator_tokens,
    iter_selected_families,
    load_manifest,
    repo_root_for_manifest,
    resolve_manifest_path,
    resolve_repo_path,
)


def command_for_generator(generator: str, repo_root: Path) -> list[str]:
    tokens = generator_tokens(generator)
    if not tokens:
        raise ValueError("Empty generator command")

    first = tokens[0]
    if first.endswith(".py") or "/" in first:
        return [sys.executable, str(resolve_repo_path(first, repo_root)), *tokens[1:]]

    if first in {"python", "python3"} and len(tokens) > 1:
        script = tokens[1]
        if script.endswith(".py") or "/" in script:
            return [sys.executable, str(resolve_repo_path(script, repo_root)), *tokens[2:]]

    return tokens


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--family", action="append", help="Run one family. Repeatable.")
    parser.add_argument(
        "--status",
        action="append",
        default=None,
        help="Run families with this status. Defaults to implemented. Repeatable.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--continue-on-error", action="store_true", help="Keep running after a command fails.")
    args = parser.parse_args(argv)

    manifest_path = resolve_manifest_path(args.manifest)
    repo_root = repo_root_for_manifest(manifest_path)
    manifest = load_manifest(manifest_path)

    statuses = set(args.status) if args.status else {"implemented"}
    families = iter_selected_families(
        manifest,
        names=set(args.family) if args.family else None,
        statuses=statuses,
    )

    if not families:
        print("No figure families selected.")
        return 0

    failures: list[tuple[str, int]] = []
    for name, spec in families:
        generator = str(spec.get("generator") or "")
        if not generator:
            print(f"Skipping {name}: no generator command.")
            continue

        command = command_for_generator(generator, repo_root)
        printable = " ".join(shlex.quote(part) for part in command)
        print(f"{name}: {printable}")

        if args.dry_run:
            continue

        completed = subprocess.run(command, cwd=repo_root)
        if completed.returncode != 0:
            failures.append((name, completed.returncode))
            if not args.continue_on_error:
                return completed.returncode

    if failures:
        print("\nFailed figure families:")
        for name, returncode in failures:
            print(f"  {name}: exit {returncode}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
