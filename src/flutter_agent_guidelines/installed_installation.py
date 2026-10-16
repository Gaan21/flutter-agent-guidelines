"""Small, merge-preserving project connection for installed guidance."""

from contextlib import nullcontext
import difflib
from importlib import resources
import json
import os
from pathlib import Path
import re
import shlex
import sys

from . import installed
from .hook_reviews import settings_sources
from .runtime_io import locked, read_json, save_bytes, save_json
from .snapshots import SnapshotError, canonical, checked_path, digest, regular_bytes, require_digest

SETTINGS = ".claude/settings.local.json"
PLUGIN = ".opencode/plugins/flutter-guidelines-installed.js"
EVENTS = ("SessionStart", "UserPromptSubmit")


def record_path(repo):
    return checked_path(installed.root(repo) / "connection.json")


def record(repo):
    value = read_json(record_path(repo))
    if (not isinstance(value, dict) or set(value) != {"schema", "runtime", "group", "plugin"}
            or type(value["schema"]) is not int or value["schema"] != 1
            or value["runtime"] not in ("claude", "opencode", "both")
            or not isinstance(value["group"], dict)):
        raise SnapshotError("invalid installed connection record")
    if value["plugin"] is not None:
        require_digest(value["plugin"])
    if value["runtime"] in ("opencode", "both") and value["plugin"] is None:
        raise SnapshotError("missing installed adapter fingerprint")
    return value


def group():
    # Claude command hooks use a shell command string; quote the fixed interpreter path.
    command = shlex.join([sys.executable, "-I", "-m", "flutter_agent_guidelines.cli",
                          "installed-hook", "--runtime", "claude"])
    return {"hooks": [{"type": "command", "command": command, "timeout": 30}]}


def settings(repo):
    path = checked_path(repo / SETTINGS)
    value = read_json(path) if path.exists() else {}
    if not isinstance(value, dict) or not isinstance(value.get("hooks", {}), dict):
        raise SnapshotError("invalid Claude settings")
    if any(not isinstance(value.get("hooks", {}).get(event, []), list) for event in EVENTS):
        raise SnapshotError("invalid Claude entry hook groups")
    return value


def verify_connection(repo, required=True):
    if not record_path(repo).exists():
        if required:
            raise SnapshotError("installed connection absent; run install --apply")
        return "absent"
    value = record(repo)
    if value["runtime"] in ("claude", "both"):
        hooks = settings(repo).get("hooks", {})
        if any(hooks.get(event, []).count(value["group"]) != 1 for event in EVENTS):
            raise SnapshotError("installed Claude entry hook missing/duplicated")
    if value["runtime"] in ("opencode", "both"):
        if digest(regular_bytes(checked_path(repo / PLUGIN))) != value["plugin"]:
            raise SnapshotError("installed OpenCode adapter changed; inspect before reinstall")
    findings = conflicts(repo, value["runtime"], value)
    if findings:
        raise SnapshotError("possible competing loader: " + ", ".join(findings))
    return "verified"


def hook_inventory(repo):
    """Installed-mode inventory of every Claude event; legacy inventory stays fixed."""
    result = []
    for source, path in settings_sources(repo):
        if not path.exists():
            continue
        value = read_json(path)
        if not isinstance(value, dict) or not isinstance(value.get("hooks", {}), dict):
            raise SnapshotError(f"invalid Claude settings: {path}")
        for event, groups in value.get("hooks", {}).items():
            if not isinstance(groups, list):
                raise SnapshotError(f"invalid Claude hook groups: {source}:{event}")
            for group in groups:
                if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                    raise SnapshotError(f"invalid Claude hook group: {source}:{event}")
                selector = {key: item for key, item in group.items() if key != "hooks"}
                for handler in group["hooks"]:
                    if not isinstance(handler, dict):
                        raise SnapshotError(f"invalid Claude hook handler: {source}:{event}")
                    result.append({"source": source, "event": event, "selector": selector,
                        "handler": handler, "digest": digest(canonical({
                            "selector": selector, "handler": handler}))})
    return result


def claude_conflicts(repo, owned=None):
    findings = []
    for _, path in settings_sources(repo):
        if path.exists():
            value = read_json(path)
            if not isinstance(value, dict):
                raise SnapshotError(f"invalid Claude settings: {path}")
            if value.get("disableAllHooks") or value.get("allowManagedHooksOnly"):
                findings.append(str(path) + ": hooks disabled/restricted")
    for item in hook_inventory(repo):
        candidate = {**item["selector"], "hooks": [item["handler"]]}
        if (owned and owned["runtime"] in ("claude", "both") and
                item["source"] == SETTINGS and candidate == owned["group"]):
            continue
        # Ordinary tool guards coexist without fingerprint leases. Entry loaders and
        # recognizable instruction injection require explicit resolution, not a waiver.
        if item["event"] in EVENTS or re.search(
                r"additionalContext|system\.transform|flutter(?:[-_]agent)?[-_]guidelines|instructions",
                json.dumps(item["handler"]), re.I):
            findings.append(f"{item['source']}:{item['event']}")
    for name in ("CLAUDE_CODE_SIMPLE", "CLAUDE_CODE_SAFE_MODE"):
        if os.environ.get(name) not in (None, "", "0", "false"):
            findings.append(name + ": native integration disabled")
    return findings


def opencode_conflicts(repo, owned=None):
    findings = []
    home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "opencode"
    for directory in (repo / ".opencode/plugins", repo / ".opencode/plugin",
                      home / "plugins", home / "plugin"):
        directory = checked_path(directory)
        if directory.exists():
            for path in directory.iterdir():
                if path.suffix not in (".js", ".ts", ".mjs"):
                    continue
                if path == repo / PLUGIN and owned and owned["runtime"] in ("opencode", "both"):
                    continue
                text = regular_bytes(path).decode("utf-8")
                if any(term in text for term in ("system.transform", "additionalContext",
                                                 "chat.message", "instructions")):
                    findings.append(str(path))
    configs = [repo / name for name in ("opencode.json", "opencode.jsonc",
                ".opencode/opencode.json", ".opencode/opencode.jsonc")]
    configs += [home / "opencode.json", home / "opencode.jsonc"]
    if os.environ.get("OPENCODE_CONFIG"):
        configs.append(Path(os.environ["OPENCODE_CONFIG"]))
    for path in configs:
        if checked_path(path).exists() and re.search(
                r'"(?:plugins?|instructions)"\s*:', regular_bytes(path).decode("utf-8")):
            findings.append(str(path) + ": inventory plugin/instructions first")
    if os.environ.get("OPENCODE_CONFIG_CONTENT"):
        findings.append("OPENCODE_CONFIG_CONTENT: inventory external loader first")
    for name in ("OPENCODE_PURE", "OPENCODE_DISABLE_PROJECT_CONFIG"):
        if os.environ.get(name) not in (None, "", "0", "false"):
            findings.append(name + ": native integration disabled")
    return findings


def conflicts(repo, runtime="both", owned=None):
    if runtime not in ("claude", "opencode", "both"):
        raise SnapshotError("invalid installed runtime")
    findings = []
    if runtime in ("claude", "both"):
        findings.extend(claude_conflicts(repo, owned))
    if runtime in ("opencode", "both"):
        findings.extend(opencode_conflicts(repo, owned))
    return findings


def plan(repo, runtime, replacing=None, remove=False):
    if runtime not in ("claude", "opencode", "both"):
        raise SnapshotError("invalid installed runtime")
    findings = conflicts(repo, runtime, replacing)
    if findings and not remove:
        raise SnapshotError("possible competing loader; inventory before install: " + ", ".join(findings))
    changes = {}
    owned_group = group()
    if runtime in ("claude", "both"):
        value = settings(repo)
        hooks = value.setdefault("hooks", {})
        for event in EVENTS:
            groups = hooks.setdefault(event, [])
            if not isinstance(groups, list):
                raise SnapshotError("invalid Claude hook groups")
            if replacing:
                if groups.count(replacing["group"]) != 1:
                    raise SnapshotError("owned hook changed; inspect before replacing")
                groups.remove(replacing["group"])
            if not remove:
                groups.append(owned_group)
            if not groups:
                hooks.pop(event)
        changes[SETTINGS] = canonical(value)
    plugin_hash = None
    if runtime in ("opencode", "both"):
        path = checked_path(repo / PLUGIN)
        if replacing:
            if digest(regular_bytes(path)) != replacing["plugin"]:
                raise SnapshotError("owned adapter changed; inspect before replacing")
        elif path.exists():
            raise SnapshotError("unowned installed adapter exists")
        template = resources.files("flutter_agent_guidelines").joinpath(
            "adapters/opencode-installed.js").read_text(encoding="utf-8")
        launcher = [sys.executable, "-I", "-m", "flutter_agent_guidelines.cli",
                    "installed-hook", "--runtime", "opencode"]
        content = template.replace("__LAUNCHER__", json.dumps(launcher)).encode()
        changes[PLUGIN] = None if remove else content
        plugin_hash = digest(content)
    ignore = checked_path(repo / ".gitignore")
    before = regular_bytes(ignore) if ignore.exists() else b""
    lines = [b"/.flutter-guidelines-installed/", b"/.claude/settings.local.json",
             b"/.opencode/plugins/flutter-guidelines-installed.js"]
    missing = [line for line in lines if line not in before.splitlines()]
    if missing and not remove:
        changes[".gitignore"] = before + (b"\n" if before and not before.endswith(b"\n") else b"") + b"\n".join(missing) + b"\n"
    diffs = {}
    for name, content in changes.items():
        path = checked_path(repo / name)
        old = regular_bytes(path) if path.exists() else b""
        diffs[name] = "".join(difflib.unified_diff(old.decode().splitlines(True),
            (content or b"").decode().splitlines(True), fromfile=name, tofile=name + " (proposed)"))
    return {"changes": changes, "diffs": diffs,
            "record": {"schema": 1, "runtime": runtime, "group": owned_group, "plugin": plugin_hash}}


def write(repo, changes):
    # Recovery record precedes owned writes. Interrupted application is detected by verification.
    save_json(record_path(repo), changes["record"])
    for name, content in changes["changes"].items():
        path = checked_path(repo / name)
        path.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            path.unlink()
        else:
            save_bytes(path, content)


def install(repo, runtime="both", apply=False):
    installed.exclusive(repo)
    with locked(installed.root(repo)) if apply else nullcontext():
        installed.verify(repo, materialize=apply, allow_absent=not apply)
        if record_path(repo).exists():
            old = record(repo)
            verify_connection(repo)
            if old["runtime"] != runtime:
                raise SnapshotError("uninstall before changing selected clients")
            return {"apply": apply, "installation": "already installed"}
        changes = plan(repo, runtime)
        if apply:
            write(repo, changes)
        return {"apply": apply, "diffs": changes["diffs"], "restart_required": True,
                "hook_inventory": hook_inventory(repo) if runtime in ("claude", "both") else []}


def uninstall(repo, apply=False):
    with locked(installed.root(repo)) if apply else nullcontext():
        old = record(repo)
        changes = plan(repo, old["runtime"], replacing=old, remove=True)
        if apply:
            write(repo, changes)
            record_path(repo).unlink()
        return {"apply": apply, "diffs": changes["diffs"], "restart_required": True,
                "retained": [installed.PIN, installed.STATE, ".gitignore entries"]}
