"""Explicit local install plans, guarded backups and reversible owned changes."""

from importlib import resources
from contextlib import nullcontext
import base64
import difflib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from .git_source import validate_source
from .hook_reviews import (REVIEW_PURPOSE, guard_approved, hook_inventory, missing_reviews,
                           settings_sources)
from .policies import native_policies, validate_paths
from .runtime import configuration, controller_identity, load_work
from .runtime_io import consumer_root, locked, read_json, save_bytes, save_json, state_root
from .snapshots import SnapshotError, canonical, checked_path, digest, regular_bytes, require_digest

EVENTS = ("SessionStart", "UserPromptSubmit", "PreToolUse", "SessionEnd")
OWNED_PATHS = {".claude/settings.local.json", ".opencode/plugins/flutter-guidelines.js", ".gitignore"}


def installation_record(repo):
    record = read_json(state_root(repo) / "installation.json")
    if (not isinstance(record, dict) or set(record) != {
            "schema", "controller", "runtime", "files"} or record["schema"] != 1 or
            record["runtime"] not in ("claude", "opencode", "both") or
            not isinstance(record["files"], dict) or not record["files"] or
            set(record["files"]) - OWNED_PATHS):
        raise SnapshotError("invalid installation record")
    for owned in record["files"].values():
        if not isinstance(owned, dict) or set(owned) != {"before", "before_hash", "after"}:
            raise SnapshotError("invalid installation backup")
        require_digest(owned["after"])
        if owned["before"] is not None:
            before = base64.b64decode(owned["before"], validate=True)
            if digest(before) != require_digest(owned["before_hash"]):
                raise SnapshotError("backup integrity mismatch")
        elif owned["before_hash"] is not None:
            raise SnapshotError("unexpected backup hash")
    return record


def probe(command):
    try:
        result = subprocess.run([command, "--version"], capture_output=True,
                                text=True, timeout=10, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def doctor(repo):
    config = configuration(repo)
    installed = (state_root(repo) / "installation.json").exists()
    if installed:
        from .adapters import verify_adapter
        verify_adapter(repo, {})
    result = {"controller": controller_identity(), "python": sys.version.split()[0],
             "git": probe("git"), "claude": probe("claude"),
             "opencode": probe("opencode"), "node": probe("node"),
             "installation": "verified" if installed else "absent"}
    result["mode"] = "automatic" if config.get("updates") else "content-only"
    if config.get("updates") and load_work(repo):
        from .bootstrap import command
        work = command(repo, ["status", "--repo", str(repo)])["work"]
        result["active_work"] = {"revision": work["revision"], "controller": work["controller"],
                                 "snapshot": work["snapshot"]}
    return result


def configure(repo, source, policies, overlays, cache=None, apply=False, auto_update=False):
    repo = consumer_root(repo)
    from . import installed
    if installed.enabled(repo):
        raise SnapshotError("installed project pin exists; explicitly disconnect and archive it before legacy configuration")
    validate_source(source)
    validate_paths(policies)
    validate_paths(overlays)
    config = {"schema": 1, "source": source,
               "policies": sorted(set(policies) | set(native_policies(repo))), "overlays": overlays}
    if auto_update:
        config["updates"] = {"protocol": 1}
    if cache:
        config["cache"] = str(checked_path(cache))
    path = checked_path(repo / ".flutter-guidelines.json")
    if path.exists():
        existing = configuration(repo)
        if "reviewed_guards" in existing:
            config["reviewed_guards"] = existing["reviewed_guards"]
        if existing != config:
            if load_work(repo) or (state_root(repo) / "installation.json").exists():
                raise SnapshotError("close work and uninstall integration before reconfiguring")
            if apply:
                save_json(path, config)
    elif apply:
        save_json(path, config)
    return {"apply": apply, "path": str(path), "configuration": config}


def review_guard(repo, source, fingerprint, non_instruction_guard=False, apply=False):
    """Owner attestation after executable review; never executes or approves a loader."""
    with locked(state_root(repo)) if apply else nullcontext():
        config = configuration(repo)
        require_digest(fingerprint)
        if not non_instruction_guard:
            raise SnapshotError("explicit non-instruction guard attestation required")
        candidates = [item for item in hook_inventory(repo) if item["source"] == source and
                      item["event"] == "PreToolUse" and item["digest"] == fingerprint and
                      item["approvable"]]
        if not candidates:
            raise SnapshotError("no matching approvable PreToolUse definition; inventory hooks again")
        approval = {"source": source, "event": "PreToolUse", "digest": fingerprint,
                    "purpose": REVIEW_PURPOSE}
        reviews = config.setdefault("reviewed_guards", [])
        if approval not in reviews:
            if load_work(repo):
                raise SnapshotError("close work before changing reviewed guards")
            reviews.append(approval)
        if apply:
            save_json(repo / ".flutter-guidelines.json", config)
        return {"apply": apply, "review": approval, "definition": candidates[0]}


def claude_hook_group(event="PreToolUse", managed=False):
    return {"hooks": [{"type": "command", "command": sys.executable,
                        "args": ["-I", "-m", "flutter_agent_guidelines.cli", "bridge" if managed else "hook", "--runtime", "claude"],
                       "onFailure": "block" if event == "PreToolUse" else "continue", "timeout": 120}]}


def conflicts(repo):
    findings = []
    claude_home = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    opencode_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "opencode"
    # Conservative inventory: unknown instruction-injecting hooks/plugins require review.
    reviews = configuration(repo, discover_policies=False).get("reviewed_guards", [])
    inventory = hook_inventory(repo)
    findings.extend(missing_reviews(inventory, reviews))
    for _, path in settings_sources(repo):
        if path.exists():
            value = read_json(path)
            if value.get("disableAllHooks") or value.get("allowManagedHooksOnly"):
                findings.append(str(path) + ": repository hooks disabled/restricted")
    for item in inventory:
        owned = (item["source"] == ".claude/settings.local.json" and
                 (state_root(repo) / "installation.json").exists() and
                  {**item["selector"], "hooks": [item["handler"]]} == claude_hook_group(
                      item["event"], bool(configuration(repo, discover_policies=False).get("updates"))))
        if not owned and not guard_approved(item, reviews):
            findings.append(f"{item['source']}:{item['event']} sha256={item['digest']} "
                            f"({'review non-instruction guard' if item['approvable'] else 'not waivable'})")
    for directory in (repo / ".opencode/plugins", repo / ".opencode/plugin",
                      opencode_home / "plugins", opencode_home / "plugin"):
        root = checked_path(directory)
        if root.exists():
            for path in root.iterdir():
                if (path.suffix in (".js", ".ts") and
                        path != repo / ".opencode/plugins/flutter-guidelines.js"):
                    text = regular_bytes(path).decode("utf-8")
                    if any(term in text for term in ("system.transform", "additionalContext",
                                                     "chat.message", "instructions")):
                        findings.append(str(path))
    config_paths = [repo / name for name in ("opencode.json", "opencode.jsonc",
                   ".opencode/opencode.json", ".opencode/opencode.jsonc")]
    config_paths.extend(opencode_home / name for name in ("opencode.json", "opencode.jsonc"))
    if os.environ.get("OPENCODE_CONFIG"):
        config_paths.append(Path(os.environ["OPENCODE_CONFIG"]))
    if os.environ.get("OPENCODE_CONFIG_CONTENT"):
        findings.append("OPENCODE_CONFIG_CONTENT requires external loader inventory")
    for candidate in config_paths:
        path = checked_path(candidate)
        if path.exists():
            text = regular_bytes(path).decode("utf-8")
            if re.search(r'"(?:plugins?|instructions)"\s*:', text):
                findings.append(str(path) + ": plugin/instructions require inventory")
    # Native instruction files may delegate to a second authority without hooks.
    for candidate in (repo / name for name in native_policies(repo)):
        if candidate.exists():
            text = regular_bytes(candidate).decode("utf-8")
            references = re.findall(r"(?:@|\]\()([^\s)]+(?:AGENTS|CLAUDE)\.md)", text)
            for reference in references:
                target = (candidate.parent / reference).resolve()
                if "://" in reference or (repo != target and repo not in target.parents):
                    findings.append(str(candidate) + ": external instruction delegation")
    for candidate in (claude_home / "CLAUDE.md", claude_home / "rules", opencode_home / "AGENTS.md"):
        if candidate.exists():
            findings.append(str(candidate) + ": external auto-loaded authority requires inventory")
    for key in ("OPENCODE_PURE", "OPENCODE_DISABLE_PROJECT_CONFIG", "CLAUDE_CODE_SIMPLE",
                "CLAUDE_CODE_SAFE_MODE"):
        if os.environ.get(key) not in (None, "", "0", "false"):
            findings.append(key + ": native integration disabled")
    return findings


def desired(repo, runtime):
    changes = {}
    managed = bool(configuration(repo, discover_policies=False).get("updates"))
    launcher = [sys.executable, "-I", "-m", "flutter_agent_guidelines.cli", "bridge" if managed else "hook"]
    if runtime in ("both", "claude"):
        version = probe("claude")
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", version or "")
        if not match or tuple(map(int, match.groups())) < (2, 1, 295):
            raise SnapshotError("Claude >=2.1.295 required for fail-closed hooks")
        path = repo / ".claude/settings.local.json"
        settings = read_json(path) if path.exists() else {}
        hooks = settings.setdefault("hooks", {})
        for event in EVENTS:
            hooks.setdefault(event, []).append(claude_hook_group(event, managed))
        changes[".claude/settings.local.json"] = canonical(settings)
    if runtime in ("both", "opencode"):
        template = resources.files("flutter_agent_guidelines").joinpath(
            "adapters/opencode-bootstrap.js" if managed else "adapters/opencode.js").read_text(encoding="utf-8")
        changes[".opencode/plugins/flutter-guidelines.js"] = template.replace(
            "__LAUNCHER__", json.dumps(launcher + ["--runtime", "opencode"])).encode()
    ignore = repo / ".gitignore"
    content = regular_bytes(ignore) if ignore.exists() else b""
    additions = [name for name in ("/.flutter-guidelines/", "/.flutter-guidelines.json",
                                   "/.claude/settings.local.json",
                                   "/.opencode/plugins/flutter-guidelines.js")
                 if name.encode() not in content.splitlines()]
    if additions:
        changes[".gitignore"] = content + (b"\n" if content and not content.endswith(b"\n") else b"") + (
            "\n".join(additions) + "\n").encode()
    return changes


def install(repo, runtime="both", apply=False):
    root = state_root(repo)
    with locked(root) if apply else nullcontext():
        configuration(repo)
        record = root / "installation.json"
        if record.exists():
            existing = installation_record(repo)
            for name, owned in existing["files"].items():
                if digest(regular_bytes(repo / name)) != owned["after"]:
                    raise SnapshotError(f"owned file changed; inspect backup: {name}")
            if existing["controller"] != controller_identity() or existing["runtime"] != runtime:
                raise SnapshotError("uninstall previous integration before changing controller/runtime")
            findings = conflicts(repo)
            if findings:
                raise SnapshotError("coexistence review invalid: " + ", ".join(findings))
            return {"apply": apply, "state": "already installed", "files": list(existing["files"])}
        findings = conflicts(repo)
        if findings:
            raise SnapshotError("possible competing loader; inventory before install: " + ", ".join(findings))
        changes = desired(repo, runtime)
        if load_work(repo):
            raise SnapshotError("close existing work before installation")
        files = {}
        diffs = {}
        for name, content in changes.items():
            path = checked_path(repo / name)
            before = regular_bytes(path) if path.exists() else None
            if name.endswith("flutter-guidelines.js") and before is not None:
                raise SnapshotError("unowned plugin exists")
            files[name] = {"before": base64.b64encode(before).decode() if before is not None else None,
                           "before_hash": digest(before) if before is not None else None,
                           "after": digest(content)}
            diffs[name] = "".join(difflib.unified_diff(
                (before or b"").decode("utf-8").splitlines(keepends=True),
                content.decode("utf-8").splitlines(keepends=True),
                fromfile=name + " (before)", tofile=name + " (installed)"))
        if apply:
            # Record recovery material before any owned write. Partial installs fail closed.
            save_json(record, {"schema": 1, "controller": controller_identity(),
                               "runtime": runtime, "files": files})
            for name, content in changes.items():
                path = checked_path(repo / name)
                path.parent.mkdir(parents=True, exist_ok=True)
                save_bytes(path, content)
        return {"apply": apply, "files": list(files), "diffs": diffs, "restart_required": True}


def uninstall(repo, apply=False):
    root = state_root(repo)
    with locked(root) if apply else nullcontext():
        if load_work(repo):
            raise SnapshotError("close work and release sessions before uninstall")
        record = installation_record(repo)
        for name, owned in record["files"].items():
            if digest(regular_bytes(repo / name)) != owned["after"]:
                raise SnapshotError(f"user-modified file; backup retained, inspect: {name}")
            if owned["before"] is not None:
                if digest(base64.b64decode(owned["before"], validate=True)) != owned["before_hash"]:
                    raise SnapshotError("backup integrity mismatch")
        if apply:
            for name, owned in record["files"].items():
                path = checked_path(repo / name)
                if owned["before"] is None:
                    path.unlink()
                else:
                    before = base64.b64decode(owned["before"], validate=True)
                    if digest(before) != owned["before_hash"]:
                        raise SnapshotError("backup integrity mismatch")
                    save_bytes(path, before)
            (root / "installation.json").unlink()
        return {"apply": apply, "restored": list(record["files"])}
