"""Atomic, dependency-free controller deployments from an explicitly approved Git source."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

from .bundles import NOTICES, PAYLOAD
from .git_source import git, validate_source
from .runtime_io import locked, read_json, save_json
from .snapshots import (SnapshotError, canonical, checked_path, digest, regular_bytes,
                        require_digest, verify_snapshot, write_snapshot)

PROTOCOL = 1
CONTRACT = {"protocol": PROTOCOL, "engine": "flutter_agent_guidelines.engine",
            "opencode": "adapters/opencode.js"}
PREFIX = "src/flutter_agent_guidelines/"


def invoke(path, request):
    """Fresh isolated interpreter; never replace modules in the bootstrap process."""
    program = ("import sys,runpy; sys.path.insert(0,sys.argv[1]); "
               "runpy.run_module('flutter_agent_guidelines.engine',run_name='__main__')")
    environment = dict(os.environ, FLUTTER_GUIDELINES_DEPLOYMENT=str(path))
    try:
        result = subprocess.run([sys.executable, "-I", "-B", "-c", program, str(path / "package")],
                                input=json.dumps(request), text=True, capture_output=True,
                                env=environment, timeout=100)
    except subprocess.SubprocessError as error:
        raise SnapshotError("controller interrupted/timed out; inspect its lock before recovery") from error
    if result.returncode:
        raise SnapshotError("controller failed: " + (result.stderr.strip() or str(result.returncode)))
    try:
        response = json.loads(result.stdout)
    except ValueError as error:
        raise SnapshotError("invalid controller protocol response") from error
    if not isinstance(response, dict):
        raise SnapshotError("invalid controller response")
    return response


def verify_deployment(path, source, revision):
    path = checked_path(path)
    manifest = verify_snapshot(path, path.name)
    if manifest["metadata"] != {"kind": "controller", "protocol": PROTOCOL,
                                "source_url": source["url"], "revision": revision}:
        raise SnapshotError("controller deployment authority/revision mismatch")
    contract = json.loads(regular_bytes(path / "package/flutter_agent_guidelines/bootstrap-contract.json"))
    if contract != CONTRACT:
        raise SnapshotError("incompatible bootstrap protocol; close work, migrate bootstrap and restart clients")
    return manifest


def source_files(source, revision, cache):
    """Fetch an exact object and read regular blobs; no checkout/setup/build hooks."""
    objects = checked_path(cache / "controller-git" / digest(source["url"].encode()))
    if not objects.exists():
        objects.parent.mkdir(parents=True, exist_ok=True)
        git("init", "--bare", objects)
    git("--git-dir", objects, "fetch", "--no-tags", "--depth=1", "--", source["url"], revision)
    if git("--git-dir", objects, "rev-parse", "FETCH_HEAD^{commit}").decode().strip() != revision:
        raise SnapshotError("controller fetch differs from resolved revision")
    files = {}
    for entry in git("--git-dir", objects, "ls-tree", "-rz", revision).split(b"\0"):
        if not entry:
            continue
        header, raw_name = entry.split(b"\t", 1)
        name = raw_name.decode("utf-8")
        relative = name.removeprefix(PREFIX)
        selected = (name in {*NOTICES, "pyproject.toml"} or name.startswith(PREFIX) and
                    (re.fullmatch(r"[a-z_]+\.py", relative) or
                     relative in {"bootstrap-contract.json", "adapters/opencode.js",
                                  "adapters/opencode-bootstrap.js"} or
                     relative in {"payload/" + item for item in PAYLOAD}))
        if selected:
            mode, kind, oid = header.decode().split()
            if mode != "100644" or kind != "blob":
                raise SnapshotError("nonregular controller source: " + name)
            files[name] = git("--git-dir", objects, "cat-file", "blob", oid)
    return files


def deployment_files(files):
    try:
        project = tomllib.loads(files["pyproject.toml"].decode())["project"]
        contract = json.loads(files[PREFIX + "bootstrap-contract.json"])
        version = project["version"]
        minimum = re.fullmatch(r">=3\.(\d+)", project["requires-python"])
        if (project["name"] != "flutter-agent-guidelines" or project.get("dependencies", []) or
                not re.fullmatch(r"\d+\.\d+\.\d+(?:\.dev\d+)?", version) or not minimum or
                sys.version_info < (3, int(minimum[1])) or contract != CONTRACT):
            raise SnapshotError("incompatible deployment; migrate bootstrap/Python and restart clients")
        required = {PREFIX + "engine.py", PREFIX + "__init__.py", PREFIX + "adapters/opencode.js",
                    *(PREFIX + "payload/" + name for name in PAYLOAD), *NOTICES}
        if not required <= files.keys():
            raise SnapshotError("incomplete controller source")
    except (KeyError, ValueError, TypeError) as error:
        raise SnapshotError("missing or incompatible controller contract; update bootstrap explicitly") from error
    output = {"package/flutter_agent_guidelines/" + name.removeprefix(PREFIX): value
              for name, value in files.items() if name.startswith(PREFIX)}
    for name, value in output.items():
        if name.endswith(".py"):
            try:
                compile(value, name, "exec")
            except SyntaxError as error:
                raise SnapshotError("controller is incompatible with installed Python: " + name) from error
    info = "package/flutter_agent_guidelines-" + version + ".dist-info/"
    output[info + "METADATA"] = ("Metadata-Version: 2.4\nName: flutter-agent-guidelines\n"
                                  f"Version: {version}\n").encode()
    for name in NOTICES:
        output[info + "licenses/" + name] = files[name]
        output["bundle/" + name] = files[name]
    for name in PAYLOAD:
        output["bundle/payload/" + name] = files[PREFIX + "payload/" + name]
    output[info + "RECORD"] = "".join(name.removeprefix("package/") + ",,\n"
                                         for name in output if name.startswith("package/")).encode()
    return output


def prepare(source, revision, cache):
    validate_source(source)
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise SnapshotError("exact controller revision required")
    cache = checked_path(cache)
    root = checked_path(cache / "controllers")
    with locked(root):
        index = checked_path(root / (digest(canonical([source["url"], revision])) + ".json"))
        if index.exists():
            target = root / require_digest(read_json(index)["digest"])
            verify_deployment(target, source, revision)
            return target
        files = deployment_files(source_files(source, revision, cache))
        # A killed process leaves an unreferenced staging directory, never a live deployment.
        staging = Path(tempfile.mkdtemp(prefix="staging-", dir=root))
        try:
            candidate = write_snapshot(staging, files, {"kind": "controller", "protocol": PROTOCOL,
                                       "source_url": source["url"], "revision": revision})
            probe = invoke(candidate, {"kind": "probe"})
            if probe.get("protocol") != PROTOCOL:
                raise SnapshotError("controller protocol probe failed; restart after explicit migration")
            target = root / candidate.name
            if target.exists():
                verify_deployment(target, source, revision)
            else:
                # macOS requires write permission on the directory being renamed.
                candidate.chmod(0o755)
                os.replace(candidate, target)
                target.chmod(0o555)
            save_json(index, {"digest": target.name})
            return target
        finally:
            # Published directories are never removed. Stale interrupted staging is operator-owned.
            for directory, _, _ in os.walk(staging):
                os.chmod(directory, 0o700)
            shutil.rmtree(staging)
