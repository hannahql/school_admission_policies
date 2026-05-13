#!/usr/bin/env python3
"""Report cache and generator availability for paper figure families.

The manifest is intentionally simple YAML. If PyYAML is installed, this script
uses it. Otherwise it falls back to a small parser that supports the subset used
by reproduce_figures/manifest.yaml.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = "reproduce_figures/manifest.yaml"


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_limited_yaml(text: str) -> dict[str, Any]:
    """Parse the restricted YAML shape used by the figure manifest."""

    data: dict[str, Any] = {}
    in_families = False
    current_family: str | None = None
    current_list_key: str | None = None

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indent == 0:
            current_family = None
            current_list_key = None
            if line.endswith(":"):
                key = line[:-1]
                if key == "figure_families":
                    data[key] = {}
                    in_families = True
                else:
                    data[key] = {}
                    in_families = False
            else:
                key, sep, value = line.partition(":")
                if not sep:
                    raise ValueError(f"Cannot parse line {lineno}: {raw_line}")
                data[key] = _strip_quotes(value.strip())
                in_families = False
            continue

        if in_families and indent == 2 and line.endswith(":"):
            current_family = line[:-1]
            data["figure_families"][current_family] = {}
            current_list_key = None
            continue

        if in_families and current_family and indent == 4:
            key, sep, value = line.partition(":")
            if not sep:
                raise ValueError(f"Cannot parse line {lineno}: {raw_line}")
            value = value.strip()
            if value:
                data["figure_families"][current_family][key] = _strip_quotes(value)
                current_list_key = None
            else:
                data["figure_families"][current_family][key] = []
                current_list_key = key
            continue

        if in_families and current_family and indent == 6 and line.startswith("- "):
            if current_list_key is None:
                raise ValueError(f"List item without list key on line {lineno}: {raw_line}")
            item = _strip_quotes(line[2:].strip())
            data["figure_families"][current_family].setdefault(current_list_key, []).append(item)
            continue

        raise ValueError(f"Unsupported manifest shape on line {lineno}: {raw_line}")

    return data


def load_manifest(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        return _parse_limited_yaml(text)

    loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise ValueError(f"Manifest did not parse to a mapping: {path}")
    return loaded


def resolve_manifest_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def repo_root_for_manifest(manifest_path: Path) -> Path:
    return manifest_path.parent


def as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None and str(item) != ""]
    return [str(value)]


def resolve_repo_path(path_value: str, repo_root: Path) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return repo_root / path


def generator_tokens(generator: str | None) -> list[str]:
    if not generator:
        return []
    return shlex.split(generator)


def generator_script_path(generator: str | None, repo_root: Path) -> Path | None:
    tokens = generator_tokens(generator)
    if not tokens:
        return None

    first = tokens[0]
    if first.endswith(".py") or "/" in first:
        return resolve_repo_path(first, repo_root)

    if first in {"python", "python3"} and len(tokens) > 1:
        candidate = tokens[1]
        if candidate.endswith(".py") or "/" in candidate:
            return resolve_repo_path(candidate, repo_root)

    return None


def iter_selected_families(
    manifest: dict[str, Any],
    names: set[str] | None,
    statuses: set[str] | None,
) -> list[tuple[str, dict[str, Any]]]:
    families = manifest.get("figure_families", {})
    if not isinstance(families, dict):
        raise ValueError("Manifest field figure_families must be a mapping")

    selected: list[tuple[str, dict[str, Any]]] = []
    for name, spec in families.items():
        if names and name not in names:
            continue
        if not isinstance(spec, dict):
            raise ValueError(f"Family {name} must be a mapping")
        if statuses and str(spec.get("status", "")) not in statuses:
            continue
        selected.append((str(name), spec))
    return selected


def check_families(
    manifest: dict[str, Any],
    repo_root: Path,
    names: set[str] | None = None,
    statuses: set[str] | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for name, spec in iter_selected_families(manifest, names, statuses):
        generator = spec.get("generator")
        script_path = generator_script_path(str(generator) if generator else None, repo_root)

        missing_cache = [
            raw_path
            for raw_path in as_list(spec.get("cache_paths"))
            if not resolve_repo_path(raw_path, repo_root).exists()
        ]
        missing_optional_cache = [
            raw_path
            for raw_path in as_list(spec.get("optional_cache_paths"))
            if not resolve_repo_path(raw_path, repo_root).exists()
        ]
        missing_generator = bool(script_path and not script_path.exists())

        results.append(
            {
                "name": name,
                "status": str(spec.get("status", "")),
                "generator": str(generator or ""),
                "missing_generator": missing_generator,
                "missing_cache": missing_cache,
                "missing_optional_cache": missing_optional_cache,
                "outputs": as_list(spec.get("outputs")),
                "notes": str(spec.get("notes", "")),
            }
        )

    return results


def print_report(results: list[dict[str, Any]]) -> None:
    status_counts: dict[str, int] = {}
    for result in results:
        status_counts[result["status"]] = status_counts.get(result["status"], 0) + 1

    print("Figure input check")
    print(f"Families checked: {len(results)}")
    if status_counts:
        print("Status counts:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")

    missing_generator = [result for result in results if result["missing_generator"]]
    missing_cache = [result for result in results if result["missing_cache"]]
    missing_optional = [result for result in results if result["missing_optional_cache"]]

    if missing_generator:
        print("\nMissing generator scripts:")
        for result in missing_generator:
            print(f"  {result['name']}: {result['generator']}")

    if missing_cache:
        print("\nMissing required cache paths:")
        for result in missing_cache:
            print(f"  {result['name']}:")
            for raw_path in result["missing_cache"]:
                print(f"    {raw_path}")

    if missing_optional:
        print("\nMissing optional cache paths:")
        for result in missing_optional:
            print(f"  {result['name']}:")
            for raw_path in result["missing_optional_cache"]:
                print(f"    {raw_path}")

    if not missing_generator and not missing_cache:
        print("\nNo missing required generators or cache paths for selected families.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--family", action="append", help="Check one family. Repeatable.")
    parser.add_argument("--status", action="append", help="Check families with this status. Repeatable.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if required inputs are missing.")
    args = parser.parse_args(argv)

    manifest_path = resolve_manifest_path(args.manifest)
    repo_root = repo_root_for_manifest(manifest_path)
    manifest = load_manifest(manifest_path)

    results = check_families(
        manifest,
        repo_root,
        names=set(args.family) if args.family else None,
        statuses=set(args.status) if args.status else None,
    )
    print_report(results)

    has_missing_required = any(result["missing_generator"] or result["missing_cache"] for result in results)
    if args.strict and has_missing_required:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
