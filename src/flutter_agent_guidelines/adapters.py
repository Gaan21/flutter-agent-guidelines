"""Native hook protocol and bounded read-only guards; not an OS sandbox."""

from pathlib import Path
import json
import os
import re
import sys

from .runtime import PolicyDrift, cache_directory, configuration, controller_identity, join, lifecycle, mark_rebaseline
from .runtime_io import discover, state_root
from .snapshots import SnapshotError, digest, regular_bytes


def verify_adapter(repo, payload):
    from .installation import conflicts, installation_record
    findings = conflicts(repo)
    if findings:
        raise SnapshotError("competing/external loader requires inventory: " + ", ".join(findings))
    record = state_root(repo) / "installation.json"
    if not record.exists():
        raise SnapshotError("runtime not installed")
    installation = installation_record(repo)
    managed = configuration(repo, discover_policies=False).get("updates") and os.environ.get("FLUTTER_GUIDELINES_DEPLOYMENT")
    if managed:
        from .engine import verify_execution
        verify_execution(repo)
    elif installation["controller"] != controller_identity():
        raise SnapshotError("installation controller changed; reinstall after work closure")
    for name, owned in installation["files"].items():
        if digest(regular_bytes(repo / name)) != owned["after"]:
            raise SnapshotError(f"installed integration modified: {name}")
    if payload.get("adapter_path"):
        path = Path(payload["adapter_path"])
        expected_path = repo / ".opencode/plugins/flutter-guidelines.js"
        if path != expected_path or digest(regular_bytes(path)) != payload.get("adapter_hash"):
            raise SnapshotError("loaded OpenCode adapter differs from installed bytes")


def guard(repo, name, arguments, cwd=None):
    """Deny named protected targets, including symlink aliases. Shell stays permissioned."""
    protected = [state_root(repo).resolve(), (repo / ".flutter-guidelines.json").resolve(),
                 (repo / ".claude/settings.local.json").resolve(),
                  (repo / ".opencode/plugins/flutter-guidelines.js").resolve()]
    protected.append(Path(__file__).parent.resolve())
    if sys.prefix != sys.base_prefix:
        protected.append(Path(sys.prefix).resolve())
    try:
        protected.append(cache_directory(configuration(repo, discover_policies=False)).resolve())
    except (SnapshotError, OSError, ValueError, TypeError):
        pass  # Local protected targets remain guarded even with broken configuration.
    readonly = {"read", "glob", "grep", "list", "Read", "Glob", "Grep", "LS",
                "webfetch", "websearch", "WebFetch", "WebSearch"}
    if name in readonly:
        return

    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for child in value.values():
                yield from strings(child)
        elif isinstance(value, list):
            for child in value:
                yield from strings(child)

    for value in strings(arguments):
        # Covers structured path fields and literal patch/shell targets. Not shell interpretation.
        candidates = [value, *re.findall(r"[^\s\"'`<>|;()]+", value)]
        for candidate in candidates:
            if len(candidate) > 4096 or "\n" in candidate or "\0" in candidate:
                continue
            path = Path(candidate)
            path = (path if path.is_absolute() else Path(cwd or repo) / path).resolve()
            if any(path == root or root in path.parents for root in protected):
                raise SnapshotError("tool write/execute target is protected runtime state")


def verified_handle(runtime, payload):
    repo = discover(payload.get("cwd") or "")
    if runtime == "claude" and payload.get("hook_event_name") == "SessionEnd":
        if not payload.get("agent_id"):
            lifecycle(repo, "release", runtime, payload["session_id"],
                      payload.get("bootstrap_lease") or "process-" + str(os.getppid()))
        return {}
    if runtime == "opencode" and payload.get("event") == "release":
        if not payload.get("lease"):
            raise SnapshotError("OpenCode adapter instance lease required")
        return lifecycle(repo, "release", runtime, payload.get("session_id"), payload["lease"])
    verify_adapter(repo, payload)
    configuration(repo)
    if runtime == "claude":
        event = payload["hook_event_name"]
        session = payload["session_id"]
        lease = payload.get("bootstrap_lease") or "process-" + str(os.getppid())
        normalized = {"SessionStart": "prompt", "UserPromptSubmit": "prompt",
                      "PreToolUse": "tool"}.get(event)
        if normalized is None:
            raise SnapshotError("unsupported Claude hook event")
    else:
        normalized = "verify" if payload["event"] == "select" else payload["event"]
        session = payload.get("session_id")
        lease = payload.get("lease")
        if not lease:
            raise SnapshotError("OpenCode adapter instance lease required")
        if normalized == "doctor":
            return {"controller": controller_identity()}
    mode = ("entry" if (runtime == "claude" and event == "SessionStart") or
            (runtime == "opencode" and normalized == "verify") else
            "provenance" if runtime == "claude" and event == "UserPromptSubmit" else "none")
    result = join(repo, runtime, session, payload.get("role", "participant"),
                  payload.get("expected"), normalized == "prompt",
                  payload.get("adapter_hash") or controller_identity()["digest"], lease, mode)
    if runtime != "claude":
        return result
    if event == "PreToolUse":
        return {}
    return {"hookSpecificOutput": {"hookEventName": event,
                                   "additionalContext": result["context"]}}


def handle(runtime, payload):
    repo = discover(payload.get("cwd") or "")
    tool = (payload.get("hook_event_name") == "PreToolUse" if runtime == "claude"
            else payload.get("event") == "tool")
    if tool:
        guard(repo, payload.get("tool_name", ""), payload.get("tool_input", {}), payload.get("cwd"))
    try:
        return verified_handle(runtime, payload)
    except (SnapshotError, OSError, ValueError, KeyError, TypeError) as error:
        if isinstance(error, PolicyDrift):
            try:
                mark_rebaseline(repo)
            except (SnapshotError, OSError, ValueError, KeyError, TypeError) as state_error:
                print(f"Flutter rebaseline status could not be saved: {state_error}", file=sys.stderr)
        warning = f"Flutter guidelines unavailable; no context injected: {error}"
        if isinstance(error, PolicyDrift):
            warning += "; rebaseline required before closure/acceptance"
        print(warning, file=sys.stderr)
        if runtime == "claude":
            return {"systemMessage": warning}
        return {"warning": warning}


def hook(runtime):
    payload = {}
    try:
        payload = json.load(sys.stdin)
        print(json.dumps(handle(runtime, payload)))
        return 0
    except (SnapshotError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"flutter-guidelines: {error}", file=sys.stderr)
        if runtime == "claude" and payload.get("hook_event_name") in (
                "SessionStart", "UserPromptSubmit"):
            print(json.dumps({"systemMessage": f"Flutter guidelines unavailable; no context injected: {error}"}))
            return 0
        return 2
