"""Runtime filesystem primitives; no consumer code execution."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import time

from .snapshots import SnapshotError, canonical, checked_path, regular_bytes


def read_json(path):
    try:
        return json.loads(regular_bytes(path))
    except (ValueError, TypeError) as error:
        raise SnapshotError(f"invalid JSON: {path}") from error


def save_json(path, value):
    save_bytes(path, canonical(value))


def save_bytes(path, content):
    path = checked_path(path)
    temporary = checked_path(path.with_name(path.name + f".{os.getpid()}.tmp"))
    with temporary.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


@contextmanager
def locked(directory):
    directory = checked_path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    lock = checked_path(directory / "lock")
    deadline = time.monotonic() + 35
    while True:
        try:
            lock.mkdir()
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise SnapshotError(f"lock timeout; inspect abandoned lock: {lock}")
            time.sleep(0.05)
    try:
        yield
    finally:
        lock.rmdir()


def discover(directory):
    directory = checked_path(directory)
    for candidate in (directory, *directory.parents):
        if (candidate / ".flutter-guidelines.json").exists():
            return candidate
        if (candidate / ".git").exists():
            break
    raise SnapshotError("no consumer configuration in native cwd/worktree")


def consumer_root(repo):
    repo = checked_path(repo)
    if not repo.is_dir():
        raise SnapshotError("consumer root must be an existing directory")
    for candidate in (repo, *repo.parents):
        if (candidate / ".git").exists():
            if candidate != repo:
                raise SnapshotError(f"consumer configuration must be at worktree root: {candidate}")
            break
    return repo


def state_root(repo):
    return checked_path(consumer_root(repo) / ".flutter-guidelines")
