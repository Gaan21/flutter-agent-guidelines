"""Stable dispatch: select a controller only at a work boundary, never upgrade in place."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

from . import deployments
from .git_source import resolve, validate_source
from .runtime import cache_directory, configuration, load_work, mark_rebaseline, PolicyDrift
from .runtime_io import discover, locked, read_json, save_json, state_root
from .snapshots import SnapshotError


def enabled(repo):
    return configuration(repo, discover_policies=False).get("updates") == {"protocol": 1}


def future_source(repo, config):
    source = dict(config["source"])
    path = state_root(repo) / "future-source.json"
    if path.exists():
        override = read_json(path)
        if set(override) != {"ref"}:
            raise SnapshotError("invalid future-source selection")
        source["ref"] = override["ref"]
    return validate_source(source)


def track(repo, reference, apply=False):
    with locked(state_root(repo) / "dispatch"):
        config = configuration(repo, discover_policies=False)
        if not enabled(repo):
            raise SnapshotError("automatic executable updates require configure --auto-update")
        source = config["source"] | {"ref": reference}
        validate_source(source)
        if apply:
            save_json(state_root(repo) / "future-source.json", {"ref": reference})
        return {"apply": apply, "future_source": source, "active_work_unchanged": True}


def pointer(repo, config, work, create):
    path = state_root(repo) / "engine.json"
    if work:
        selected = read_json(path)
        if (set(selected) != {"deployment", "source_url", "revision"} or
                selected["source_url"] != work["source"]["url"] or
                selected["revision"] != work["revision"]):
            raise SnapshotError("active work/controller mismatch; never replace active selection")
        target = Path(selected["deployment"])
        expected_parent = cache_directory(config) / "controllers"
        if target.parent != expected_parent:
            raise SnapshotError("controller outside approved cache")
        deployments.verify_deployment(target, work["source"], work["revision"])
        return target
    if not create:
        return None
    source = future_source(repo, config)
    revision = source["ref"] if re.fullmatch(r"[0-9a-f]{40}", source["ref"]) else resolve(source)
    target = deployments.prepare(source, revision, cache_directory(config))
    save_json(path, {"deployment": str(target), "source_url": source["url"], "revision": revision})
    return target


def dispatch(repo, request, create=False):
    """Serialize selection through work creation, including simultaneous first sessions."""
    from .adapters import verify_adapter
    with locked(state_root(repo) / "dispatch"):
        config = configuration(repo, discover_policies=False)
        if not enabled(repo):
            raise SnapshotError("future executable source is not approved; configure --auto-update")
        payload = request.get("payload", {})
        verify_adapter(repo, payload)
        work = load_work(repo)
        bindings_path = state_root(repo) / "bindings.json"
        bindings = read_json(bindings_path) if bindings_path.exists() else {}
        native = payload.get("session_id")
        key = request.get("runtime", "") + ":" + str(native)
        if native and key in bindings:
            previous = bindings[key]
            if payload.get("expected") and previous != payload["expected"]:
                raise SnapshotError("native session has a different pinned identity")
            payload["expected"] = previous
        if not work and payload.get("expected"):
            raise SnapshotError("previous work ended; start a new native conversation")
        target = pointer(repo, config, work, create)
        if target is None:
            if request.get("argv", [None])[0] == "join":
                raise SnapshotError("explicit join requires active work")
            return {"work": None}
        response = deployments.invoke(target, request | {"repo": str(repo)})
        current = response.get("work")
        if current and current["revision"] != read_json(state_root(repo) / "engine.json")["revision"]:
            raise SnapshotError("controller prepared an unexpected content revision")
        if native and current and any(item["session"] == native and item["runtime"] == request["runtime"]
                                      for item in current["sessions"].values()):
            bindings[key] = current["snapshot"]
            save_json(bindings_path, bindings)
        result = response["result"]
        if payload.get("event") == "select" and current and not result.get("warning"):
            result["module"] = str(target / "package/flutter_agent_guidelines/adapters/opencode.js")
        return result


def command(repo, argv):
    # CLI role joins always carry --expected; lifecycle commands never prepare new work.
    return dispatch(repo, {"kind": "cli", "argv": argv}, create=False)


def handle(runtime, payload):
    from .adapters import guard
    repo = discover(payload.get("cwd") or "")
    tool = payload.get("hook_event_name") == "PreToolUse" if runtime == "claude" else payload.get("event") == "tool"
    if tool:
        guard(repo, payload.get("tool_name", ""), payload.get("tool_input", {}), payload.get("cwd"))
    # Preserve parent-session lease across the extra interpreter hop.
    if runtime == "claude":
        payload["bootstrap_lease"] = "process-" + str(os.getppid())
    release = (payload.get("hook_event_name") == "SessionEnd" if runtime == "claude"
               else payload.get("event") == "release")
    try:
        return dispatch(repo, {"kind": "hook", "runtime": runtime, "payload": payload},
                        create=not release and payload.get("event") != "doctor")
    except (SnapshotError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        if isinstance(error, PolicyDrift):
            mark_rebaseline(repo)
        warning = f"Flutter guidelines unavailable; no context injected: {error}"
        last = state_root(repo) / "engine.json"
        if last.exists():
            try:
                warning += (f"; last-known controller {read_json(last)['revision']}; "
                            "freshness UNKNOWN, no new verified work claimed")
            except (SnapshotError, OSError, KeyError, TypeError):
                pass
        print(warning, file=sys.stderr)
        return {"systemMessage" if runtime == "claude" else "warning": warning}


def hook(runtime):
    payload = {}
    try:
        payload = json.load(sys.stdin)
        print(json.dumps(handle(runtime, payload)))
        return 0
    except (SnapshotError, OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        if runtime == "claude" and payload.get("hook_event_name") in ("SessionStart", "UserPromptSubmit"):
            print(json.dumps({"systemMessage": f"Flutter guidelines unavailable; no context injected: {error}"}))
            return 0
        return 2
