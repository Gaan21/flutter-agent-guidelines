"""Offline installed-version delivery, with a portable project pin and no leases."""

from contextlib import nullcontext
import json
from pathlib import Path
import sys

from .bundles import export_bundle, inspect_package, package_files
from . import installed_contract as contracts
from .runtime import controller_identity
from .runtime_io import consumer_root, locked, save_json
from .snapshots import (SnapshotError, canonical, checked_path, digest, manifest_for,
                        regular_bytes, require_digest, verify_snapshot)

PIN = ".flutter-guidelines-installed.json"
STATE = ".flutter-guidelines-installed"
PROFILES = {"architecture": "profiles/architecture.md"}


def validate_profiles(profiles):
    if (not isinstance(profiles, list) or any(not isinstance(name, str) or name not in PROFILES
                                           for name in profiles)
            or len(set(profiles)) != len(profiles)):
        raise SnapshotError("profiles must be a list of unique supported names: architecture")
    return profiles


def root(repo):
    return checked_path(consumer_root(repo) / STATE)


def enabled(repo):
    return checked_path(repo / PIN).exists()


def identity(profiles=None, lint_contract=None):
    profiles = validate_profiles([] if profiles is None else profiles)
    info = inspect_package()
    info.pop("files")
    files = package_files()
    if any("payload/" + PROFILES[name] not in files for name in profiles):
        raise SnapshotError("selected profile is missing from installed payload")
    result = {"schema": 1, "mode": "installed", "package": info["package"],
            "version": info["version"], "payload": info["payload_digest"],
            "bundle": digest(canonical(manifest_for(files, info))),
            "controller": controller_identity()["digest"], "profiles": profiles}
    if lint_contract is not None:
        contracts.validate(lint_contract, profiles)
        result.update(lint_contract=lint_contract,
                      lint_contract_digest=digest(contracts.canonical_contract(lint_contract)))
    return result


def pin(repo):
    value = contracts.load(checked_path(repo / PIN), max_bytes=2 * contracts.MAX_BYTES)
    if (not isinstance(value, dict) or set(value) - {"profiles", "lint_contract", "lint_contract_digest"} != {
            "schema", "mode", "package", "version", "payload", "bundle", "controller"}
            or type(value["schema"]) is not int or value["schema"] != 1
            or value["mode"] != "installed" or value["package"] != "flutter-agent-guidelines"
            or not isinstance(value["version"], str) or not value["version"]):
        raise SnapshotError("invalid installed project pin")
    for name in ("payload", "bundle", "controller"):
        require_digest(value[name])
    validate_profiles(value.get("profiles", []))
    attached = {"lint_contract", "lint_contract_digest"} & set(value)
    if attached:
        if len(attached) != 2:
            raise SnapshotError("lint contract and its digest must be recorded together")
        # Read old pins independently of a new package's rule table, so an explicit
        # upgrade can replace/clear an obsolete pair without editing the old pin.
        contracts.validate(value["lint_contract"], value.get("profiles", []), align=False)
        if digest(contracts.canonical_contract(value["lint_contract"])) != require_digest(value["lint_contract_digest"]):
            raise SnapshotError("recorded lint contract digest mismatch")
    return value


def exclusive(repo):
    if checked_path(repo / ".flutter-guidelines.json").exists():
        raise SnapshotError("legacy configuration exists; explicitly migrate before installed mode")
    if checked_path(repo / ".flutter-guidelines/installation.json").exists():
        raise SnapshotError("legacy integration exists; uninstall it with its original CLI first")


def verify(repo, expected=None, materialize=False, allow_absent=False):
    exclusive(repo)
    selected = pin(repo)
    if expected is not None and digest(canonical(selected)) != require_digest(expected):
        raise SnapshotError("project identity differs from independently retained expected identity")
    actual = identity(selected.get("profiles", []), selected.get("lint_contract"))
    if "profiles" not in selected:
        # The initial installed-mode schema omitted profile selection. Retain its
        # exact identity until an explicit upgrade writes the expanded pin.
        actual.pop("profiles")
    if selected != actual:
        raise SnapshotError("installed package differs from project pin; install the pinned package "
                            "or preview upgrade-installed; pin was not changed")
    directory = root(repo) / selected["bundle"]
    if materialize:
        root(repo).mkdir(parents=True, exist_ok=True)
        export_bundle(root(repo))
    if allow_absent and not checked_path(directory).exists():
        return selected, directory
    manifest = verify_snapshot(directory, selected["bundle"])
    # Match the complete expected export, not merely a self-consistent manifest.
    info = inspect_package()
    info.pop("files")
    if manifest != manifest_for(package_files(), info):
        raise SnapshotError("project export differs from installed resources")
    return selected, directory


def configure(repo, apply=False, profiles=None, lint_contract=None, clear_lint_contract=False):
    repo = consumer_root(repo)
    supplied = contracts.load(lint_contract) if lint_contract is not None else None
    if lint_contract is not None and clear_lint_contract:
        raise SnapshotError("cannot supply and clear a lint contract together")
    if profiles is not None:
        validate_profiles(profiles)
    with locked(root(repo)) if apply else nullcontext():
        exclusive(repo)
        path = checked_path(repo / PIN)
        if not path.exists() and checked_path(root(repo) / "connection.json").exists():
            raise SnapshotError("installed connection exists without its project pin; restore the versioned pin")
        previous = pin(repo) if path.exists() else None
        selected = identity(profiles if profiles is not None else
                            previous.get("profiles", []) if previous else [],
                            contracts.attachment(previous, supplied, clear_lint_contract))
        if previous and "profiles" not in previous and profiles is None:
            selected.pop("profiles")
        if previous and previous != selected:
            raise SnapshotError("project pin differs; use upgrade-installed explicitly")
        if apply:
            export_bundle(root(repo))
            save_json(path, selected)
    return {"apply": apply, "mode": "installed", "path": str(path), "pin": selected,
            "identity": digest(canonical(selected)), "source_approval": "owner responsibility",
            "commit_pin": True}


def status(repo, expected=None):
    selected, directory = verify(repo, expected)
    from .installed_installation import verify_connection
    connection = verify_connection(repo, required=False)
    return {"mode": "installed", "pin": selected, "identity": digest(canonical(selected)),
            "guidance_root": str(directory / "payload"), "installation": connection,
            "lint_contract": contracts.summary(selected),
            "updates": "explicit package upgrade and upgrade-installed only"}


def context(repo, expected=None, include_entry=True):
    selected, directory = verify(repo, expected)
    from .installed_installation import verify_connection
    verify_connection(repo)
    profiles = selected.get("profiles", [])
    pointer = "".join(
        f"\nSelected profile: {name} ({PROFILES[name]} under the guidance root). "
        "This profile is selected for this project and must be consulted before "
        "implementation when applicable.\n" for name in profiles)
    return ("<!-- flutter-guidelines:installed -->\n"
            f"Installed Flutter guidance identity: {digest(canonical(selected))}\n"
            f"Project pin: {repo / PIN}\n"
            f"Package: {selected['package']} {selected['version']}\n"
            f"Payload SHA-256: {selected['payload']}\n"
            f"Controller SHA-256: {selected['controller']}\n"
            f"Guidance root: {directory / 'payload'}\n"
            f"Selected profiles: {', '.join(profiles) if profiles else 'none (generic guidance)'}\n"
            + contracts.description(selected) +
            "Read details there only when relevant. Native project and folder instructions "
            "retain their authority and scope. Local instructions are not snapshotted.\n\n"
            + (regular_bytes(directory / "payload/AGENTS.md").decode("utf-8") if include_entry else "")
            + pointer)


def discover(cwd):
    cwd = checked_path(cwd)
    for candidate in (cwd, *cwd.parents):
        if enabled(candidate):
            return consumer_root(candidate)
        if (candidate / ".git").exists():
            break
    raise SnapshotError("no installed project pin in native cwd/worktree")


def hook(runtime):
    try:
        if runtime not in ("claude", "opencode"):
            raise SnapshotError("unknown installed hook runtime")
        request = json.load(sys.stdin)
        repo = discover(Path(request["cwd"]))
        from .installed_installation import record
        connection = record(repo)
        if connection["runtime"] not in (runtime, "both"):
            raise SnapshotError(f"{runtime} is not selected in this installed connection")
        if runtime == "opencode":
            if request.get("adapter_hash") != connection["plugin"]:
                raise SnapshotError("loaded OpenCode adapter differs; restart the client")
        if runtime == "claude":
            event = request.get("hook_event_name")
            if event not in ("SessionStart", "UserPromptSubmit"):
                raise SnapshotError("unsupported installed hook event")
            text = context(repo, request.get("expected"), include_entry=event == "SessionStart")
            result = {"hookSpecificOutput": {"hookEventName": event,
                                              "additionalContext": text}}
        else:
            text = context(repo, request.get("expected"))
            result = {"context": text, "identity": digest(canonical(pin(repo)))}
    except (SnapshotError, OSError, ValueError, KeyError, TypeError) as error:
        warning = f"Installed Flutter guidance unavailable; no context injected: {error}"
        print(warning, file=sys.stderr)
        result = {"systemMessage": warning} if runtime == "claude" else {"warning": warning}
    print(json.dumps(result))
    return 0


def upgrade(repo, apply=False, profiles=None, lint_contract=None, clear_lint_contract=False):
    supplied = contracts.load(lint_contract) if lint_contract is not None else None
    if lint_contract is not None and clear_lint_contract:
        raise SnapshotError("cannot supply and clear a lint contract together")
    if profiles is not None:
        validate_profiles(profiles)
    from . import installed_installation as connection
    with locked(root(repo)) if apply else nullcontext():
        exclusive(repo)
        before = pin(repo)
        after = identity(before.get("profiles", []) if profiles is None else profiles,
                         contracts.attachment(before, supplied, clear_lint_contract))
        record = connection.record(repo) if connection.record_path(repo).exists() else None
        changes = connection.plan(repo, record["runtime"], replacing=record) if record else None
        # No network, package installer, or executable replacement is run here.
        if apply:
            export_bundle(root(repo))
            if changes:
                connection.write(repo, changes)
            save_json(repo / PIN, after)
    return {"apply": apply, "before": before, "after": after,
            "identity": digest(canonical(after)), "restart_required": True,
            "diffs": changes["diffs"] if changes else {}}
