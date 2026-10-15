"""Native hook protocol and bounded read-only guards; not an OS sandbox."""

from pathlib import Path
import json
import os
import re
import sys

from .runtime import configuration, controller_identity, join, lifecycle
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
    if installation["controller"] != controller_identity():
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


def handle(runtime, payload):
    repo = discover(payload.get("cwd") or "")
    verify_adapter(repo, payload)
    configuration(repo)
    if runtime == "claude":
        event = payload["hook_event_name"]
        session = payload["session_id"]
        lease = "process-" + str(os.getppid())
        # Child events carry the parent session_id; do not release its lease.
        if event == "SessionEnd":
            if not payload.get("agent_id"):
                lifecycle(repo, "release", runtime, session, lease)
            return {}
        normalized = {"SessionStart": "prompt", "UserPromptSubmit": "prompt",
                      "PreToolUse": "tool"}.get(event)
        if normalized is None:
            raise SnapshotError("unsupported Claude hook event")
    else:
        normalized = payload["event"]
        session = payload.get("session_id")
        lease = payload.get("lease")
        if not lease:
            raise SnapshotError("OpenCode adapter instance lease required")
        if normalized == "doctor":
            return {"controller": controller_identity()}
        if normalized == "release":
            return lifecycle(repo, "release", runtime, session, lease)
    mode = ("entry" if (runtime == "claude" and event == "SessionStart") or
            (runtime == "opencode" and normalized == "verify") else
            "provenance" if runtime == "claude" and event == "UserPromptSubmit" else "none")
    result = join(repo, runtime, session, payload.get("role", "participant"),
                  payload.get("expected"), normalized == "prompt",
                  payload.get("adapter_hash") or controller_identity()["digest"], lease, mode)
    if normalized == "tool":
        guard(repo, payload.get("tool_name", ""), payload.get("tool_input", {}), payload.get("cwd"))
    if runtime != "claude":
        return result
    if event == "PreToolUse":
        return {}
    return {"hookSpecificOutput": {"hookEventName": event,
                                   "additionalContext": result["context"]}}


def hook(runtime):
    try:
        payload = json.load(sys.stdin)
        print(json.dumps(handle(runtime, payload)))
        return 0
    except (SnapshotError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"flutter-guidelines: {error}", file=sys.stderr)
        # Claude exit 2 blocks prompts/tools; SessionStart additionally uses onFailure:block.
        return 2
