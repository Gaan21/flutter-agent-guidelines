"""Approved Git content only: no checkout, import, archive extraction or execution."""

import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

from .bundles import PAYLOAD, NOTICES
from .runtime_io import locked
from .snapshots import (SnapshotError, canonical, checked_path, digest,
                        relative_name, verify_snapshot, write_snapshot)


def git(*arguments):
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1",
                       GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_REPLACE_OBJECTS="1")
    for key in tuple(environment):
        if key.startswith("GIT_") and key not in {
            "GIT_TERMINAL_PROMPT", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL",
            "GIT_NO_REPLACE_OBJECTS"}:
            del environment[key]
    try:
        result = subprocess.run(["git", "-c", "core.hooksPath=" + os.devnull,
                                 "-c", "http.followRedirects=false",
                                 *map(str, arguments)], env=environment,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=25, check=True)
        return result.stdout
    except (OSError, subprocess.SubprocessError) as error:
        raise SnapshotError("Git source unavailable or command failed") from error


def validate_source(source):
    if not isinstance(source, dict) or set(source) - {"url", "ref", "trusted_fixture"}:
        raise SnapshotError("invalid source configuration")
    url, reference = source.get("url"), source.get("ref")
    if not isinstance(url, str) or not isinstance(reference, str):
        raise SnapshotError("source URL and ref required")
    try:
        parsed = urlsplit(url)
    except ValueError as error:
        raise SnapshotError("invalid source URL") from error
    fixture = source.get("trusted_fixture") is True
    if fixture:
        if not Path(url).is_absolute():
            raise SnapshotError("trusted fixture must be an explicit local directory")
        checked_path(url)
    elif (parsed.scheme != "https" or not parsed.netloc or parsed.username or
          parsed.password or parsed.query or parsed.fragment):
        raise SnapshotError("owner-approved HTTPS URL required")
    if not re.fullmatch(r"[0-9a-f]{40}", reference):
        if (not reference.startswith("refs/") or len(reference.split("/")) < 3 or
                re.search(r"[\s\x00-\x20\x7f~^:?*\[\\]", reference) or
                any(token in reference for token in ("..", "@{", "//")) or
                any(not part or part.startswith(".") or part.endswith((".", ".lock"))
                    for part in reference.split("/"))):
            raise SnapshotError("use full commit SHA or explicit refs/... channel")
    return source


def resolve(source):
    validate_source(source)
    reference = source["ref"]
    if re.fullmatch(r"[0-9a-f]{40}", reference):
        git("ls-remote", "--refs", source["url"])
        return reference
    rows = git("ls-remote", "--refs", source["url"], reference).decode().splitlines()
    matches = [row.split()[0] for row in rows if row.split()[1] == reference]
    if len(matches) != 1 or not re.fullmatch(r"[0-9a-f]{40}", matches[0]):
        raise SnapshotError("remote ref missing or ambiguous")
    return matches[0]


def materialize(source, cache):
    revision = resolve(source)
    cache = checked_path(cache)
    with locked(cache):
        objects = checked_path(cache / "git" / digest(canonical(source)))
        if not objects.exists():
            objects.parent.mkdir(parents=True, exist_ok=True)
            git("init", "--bare", objects)
        git("--git-dir", objects, "fetch", "--no-tags", "--depth=1", "--",
            source["url"], revision)
        actual = git("--git-dir", objects, "rev-parse", "FETCH_HEAD^{commit}").decode().strip()
        if actual != revision:
            raise SnapshotError("fetched revision differs from resolved commit")
        files = {}
        allowlist = {"src/flutter_agent_guidelines/payload/" + name: "payload/" + name
                     for name in PAYLOAD}
        allowlist.update({name: name for name in NOTICES})
        # Inspect modes, including parents. Symlink directories cannot be traversed.
        entries = git("--git-dir", objects, "ls-tree", "-rz", revision).split(b"\0")
        inventory = {}
        for entry in entries:
            if entry:
                header, name = entry.split(b"\t", 1)
                inventory[name.decode("utf-8")] = header.decode().split()
        for remote, local in allowlist.items():
            relative_name(local)
            mode, kind, object_id = inventory.get(remote, (None, None, None))
            if mode != "100644" or kind != "blob":
                raise SnapshotError(f"missing or nonregular public source: {remote}")
            files[local] = git("--git-dir", objects, "cat-file", "blob", object_id)
        snapshots = checked_path(cache / "snapshots")
        snapshots.mkdir(exist_ok=True)
        snapshot = write_snapshot(snapshots, files, {"source": source, "revision": revision})
        verify_snapshot(snapshot, snapshot.name)
        return revision, snapshot, files
