"""Discover native local instruction inputs without loading a rule catalog."""

import os
from pathlib import Path

from .snapshots import SnapshotError, checked_path, relative_name

GENERATED_DIRECTORIES = {".git", ".flutter-guidelines", ".dart_tool", ".venv",
                         "node_modules", "build", "__pycache__"}
ROOT_POLICIES = {"AGENTS.md", "CLAUDE.md", ".claude/CLAUDE.md"}


def validate_paths(values):
    if not isinstance(values, list) or any(not isinstance(name, str) for name in values):
        raise SnapshotError("local policy paths must be a list of strings")
    if len(values) != len(set(values)):
        raise SnapshotError("duplicate local policy path")
    for name in values:
        relative_name(name)
        if name.startswith(".flutter-guidelines/"):
            raise SnapshotError("policy cannot reference runtime state")
    return values


def policy_index(local):
    """Scope descriptors, not a selector evaluator. Keep original paths authoritative."""
    entries = []
    for pinned in sorted(local):
        _, field, logical = pinned.split("/", 2)
        path = Path(logical)
        if field == "overlays" or logical in ROOT_POLICIES:
            scope = {"kind": "global"}
        elif path.parts[:2] == (".claude", "rules"):
            scope = {"kind": "native-rule", "selector_base": ".",
                     "selectors": "Preserve native frontmatter; consult only when applicable."}
        elif path.name in ("AGENTS.md", "CLAUDE.md"):
            scope = {"kind": "ancestor-chain", "directory": path.parent.as_posix()}
        else:
            scope = {"kind": "explicit-policy", "directory": path.parent.as_posix()}
        entries.append({"logical_path": logical, "snapshot_path": pinned, "scope": scope})
    return {"schema": 1, "scope_base": "original consumer root; not snapshot directories",
            "entries": entries}


def native_policies(repo):
    result = set()
    for directory, directories, filenames in os.walk(repo, followlinks=False):
        if Path(directory).relative_to(repo).as_posix() == ".claude" and "rules" in directories:
            checked_path(Path(directory) / "rules")
        directories[:] = [name for name in directories if name not in GENERATED_DIRECTORIES]
        parent = Path(directory)
        for name in filenames:
            relative = (parent / name).relative_to(repo)
            if name in ("AGENTS.md", "CLAUDE.md") or (
                    relative.parts[:2] == (".claude", "rules") and name.endswith(".md")):
                checked_path(parent / name)
                result.add(relative.as_posix())
    return sorted(result)
