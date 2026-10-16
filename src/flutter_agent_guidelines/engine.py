"""Protocol-1 controller entry executed only after bootstrap deployment verification."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys

from .runtime_io import read_json, state_root
from .snapshots import SnapshotError, regular_bytes


def deployment():
    from .deployments import verify_deployment
    path = Path(os.environ["FLUTTER_GUIDELINES_DEPLOYMENT"])
    metadata = read_json(path / "manifest.json")["metadata"]
    verify_deployment(path, {"url": metadata["source_url"]}, metadata["revision"])
    if Path(__file__).parent != path / "package/flutter_agent_guidelines":
        raise SnapshotError("executing controller differs from selected deployment")
    return path, metadata


def materialized(config):
    path, metadata = deployment()
    if not config.get("updates") or metadata["source_url"] != config["source"]["url"]:
        raise SnapshotError("executable source was not approved")
    manifest = read_json(path / "manifest.json")
    files = {name.removeprefix("bundle/"): regular_bytes(path / name)
             for name in manifest["files"] if name.startswith("bundle/")}
    return metadata["revision"], path, files


def verify_execution(repo):
    path, metadata = deployment()
    pointer = read_json(state_root(repo) / "engine.json")
    if pointer != {"deployment": str(path), "source_url": metadata["source_url"],
                   "revision": metadata["revision"]}:
        raise SnapshotError("active controller selection mismatch")


def main():
    from .runtime import controller_identity, load_work
    request = json.load(sys.stdin)
    if request["kind"] == "probe":
        deployment()
        return {"protocol": 1, "controller": controller_identity()}
    repo = Path(request["repo"])
    verify_execution(repo)
    if request["kind"] == "hook":
        from .adapters import handle
        result = handle(request["runtime"], request["payload"])
    else:
        from .cli import main as cli
        output = io.StringIO()
        with redirect_stdout(output):
            code = cli(request["argv"])
        if code:
            raise SnapshotError("controller command rejected; inspect warning above")
        result = json.loads(output.getvalue())
    return {"result": result, "work": load_work(repo)}


if __name__ == "__main__":
    try:
        print(json.dumps(main()))
    except (SnapshotError, OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
