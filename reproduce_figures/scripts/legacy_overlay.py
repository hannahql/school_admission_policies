#!/usr/bin/env python3
"""Import helpers for wrappers that need a small amount of 2020 legacy plotting code.

The reproduction wrappers should use the maintained ``src`` implementation for
shared simulation primitives.  The vendored 2020 tree is kept only for explicitly
loaded legacy plotting files and their minimal plotting dependencies.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
DEFAULT_LEGACY_CODE_DIR = REPO_ROOT / "reproduce_figures" / "legacy_code" / "2020_sims"


def configure_overlay(legacy_code_dir: Path = DEFAULT_LEGACY_CODE_DIR) -> Path:
    """Put ``src`` ahead of the legacy tree on ``sys.path``.

    This makes imports such as ``pipeline`` and ``helpers`` resolve to the
    maintained source tree, while still allowing explicitly requested legacy
    plotting modules to be loaded from 2020 code.
    """

    legacy_code_dir = legacy_code_dir.resolve()
    if not SRC_DIR.exists():
        raise FileNotFoundError(f"Missing maintained source directory: {SRC_DIR}")
    if not legacy_code_dir.exists():
        raise FileNotFoundError(f"Missing 2020 simulation code directory: {legacy_code_dir}")

    src_text = str(SRC_DIR)
    legacy_text = str(legacy_code_dir)
    sys.path[:] = [path for path in sys.path if path not in {src_text, legacy_text}]
    sys.path.insert(0, src_text)
    sys.path.insert(1, legacy_text)
    importlib.invalidate_caches()
    return legacy_code_dir


def import_legacy_file(module_name: str, path: Path, legacy_dependency_prefixes: tuple[str, ...] = ("generic",)) -> ModuleType:
    """Import one legacy file by absolute path without making its package first.

    Legacy plotting files often import helper modules such as ``generic`` that
    are part of the old plotting stack.  For those imports, temporarily put the
    legacy tree first and restore any existing modules afterwards.  This keeps
    simulation imports pointed at ``src`` while preserving the plotting helpers'
    original dependencies.
    """

    path = path.resolve()
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load legacy module {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    legacy_code_dir = path.parents[1]
    legacy_text = str(legacy_code_dir)
    old_path = list(sys.path)
    saved_modules = {
        name: sys.modules[name]
        for name in list(sys.modules)
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in legacy_dependency_prefixes)
    }
    for name in saved_modules:
        sys.modules.pop(name, None)
    sys.path[:] = [entry for entry in sys.path if entry != legacy_text]
    sys.path.insert(0, legacy_text)
    try:
        spec.loader.exec_module(module)
    finally:
        for name in list(sys.modules):
            if any(name == prefix or name.startswith(f"{prefix}.") for prefix in legacy_dependency_prefixes):
                sys.modules.pop(name, None)
        sys.modules.update(saved_modules)
        sys.path[:] = old_path
    return module
