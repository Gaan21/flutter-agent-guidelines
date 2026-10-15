"""Content identity and filesystem checks; no publisher authentication."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat


class SnapshotError(ValueError):
    """Invalid identity, unsafe path or corrupted snapshot."""


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def digest(content):
    return hashlib.sha256(content).hexdigest()


def require_digest(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise SnapshotError("expected lowercase SHA-256")
    return value


def relative_name(name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise SnapshotError("invalid relative path")
    path = PurePosixPath(name)
    if path.is_absolute() or path.as_posix() != name:
        raise SnapshotError("noncanonical relative path")
    if any(part in (".", "..") or not re.fullmatch(r"[A-Za-z0-9_.-]+", part)
           for part in path.parts):
        raise SnapshotError("unsafe relative path")
    return path


def checked_path(path):
    """Reject links and traversal, including existing ancestor links."""
    path = Path(path).absolute()
    if ".." in path.parts:
        raise SnapshotError("path traversal rejected")
    for part in (*reversed(path.parents), path):
        if part.is_symlink():
            raise SnapshotError("symlink rejected")
    return path


def regular_bytes(path):
    path = checked_path(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise SnapshotError("expected regular file")
    return path.read_bytes()


def file_hashes(files):
    return {name: digest(content) for name, content in sorted(files.items())}


def manifest_for(files, metadata):
    for name in files:
        relative_name(name)
        if name == "manifest.json":
            raise SnapshotError("reserved manifest name")
    return {"schema": 1, "metadata": metadata, "files": file_hashes(files)}


def write_snapshot(parent, files, metadata):
    """Exclusive creation. Existing digest directories must verify exactly."""
    parent = checked_path(parent)
    if not parent.is_dir():
        raise SnapshotError("snapshot parent must already exist")
    manifest = manifest_for(files, metadata)
    identity = digest(canonical(manifest))
    target = checked_path(parent / identity)
    try:
        target.mkdir()
    except FileExistsError:
        verify_snapshot(target, identity)
        return target
    try:
        for name, content in files.items():
            output = target / name
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as stream:
                stream.write(content)
        with (target / "manifest.json").open("xb") as stream:
            stream.write(canonical(manifest))
        verify_snapshot(target, identity)
    except BaseException:
        shutil.rmtree(target)
        raise
    # Accidental-write guard only; same-user hostile races are not a sandbox.
    for entry in target.rglob("*"):
        entry.chmod(0o555 if entry.is_dir() else 0o444)
    target.chmod(0o555)
    return target


def verify_snapshot(path, expected_digest=None):
    """Offline verification, independent of installed package revision."""
    path = checked_path(path)
    require_digest(path.name)
    raw = regular_bytes(path / "manifest.json")
    identity = digest(raw)
    if identity != path.name or (expected_digest is not None and
                                identity != require_digest(expected_digest)):
        raise SnapshotError("manifest identity mismatch")
    try:
        manifest = json.loads(raw)
        if (set(manifest) != {"schema", "metadata", "files"} or
                type(manifest["schema"]) is not int or manifest["schema"] != 1
                or not isinstance(manifest["metadata"], dict)
                or not isinstance(manifest["files"], dict) or canonical(manifest) != raw):
            raise SnapshotError("invalid manifest schema or encoding")
        expected_files = {"manifest.json"}
        expected_dirs = set()
        for name, expected in manifest["files"].items():
            relative = relative_name(name)
            if name == "manifest.json":
                raise SnapshotError("reserved manifest name")
            require_digest(expected)
            if digest(regular_bytes(path / name)) != expected:
                raise SnapshotError(f"content mismatch: {name}")
            expected_files.add(name)
            expected_dirs.update(str(parent) for parent in relative.parents
                                 if str(parent) != ".")
        actual_files, actual_dirs = set(), set()
        for entry in path.rglob("*"):
            checked_path(entry)
            name = entry.relative_to(path).as_posix()
            if entry.is_dir():
                actual_dirs.add(name)
            elif stat.S_ISREG(entry.stat().st_mode):
                actual_files.add(name)
            else:
                raise SnapshotError("nonregular snapshot entry")
        if actual_files != expected_files or actual_dirs != expected_dirs:
            raise SnapshotError("unexpected snapshot inventory")
    except (TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SnapshotError("invalid manifest") from error
    return manifest
