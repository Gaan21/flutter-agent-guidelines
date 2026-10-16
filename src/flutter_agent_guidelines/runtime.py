"""One automatic role-neutral work pin per consumer worktree."""

from importlib import metadata
from pathlib import Path
import os
import re
import uuid

from .bundles import DISTRIBUTION
from .git_source import materialize, resolve, validate_source
from .policies import native_policies, policy_index, validate_paths
from .hook_reviews import hook_inventory, missing_reviews, validate_reviews
from .runtime_io import consumer_root, locked, read_json, save_json, state_root
from .snapshots import (SnapshotError, canonical, checked_path, digest, file_hashes, require_digest,
                        regular_bytes, verify_snapshot, write_snapshot)


def controller_identity():
    root = Path(__file__).parent
    files = {path.name: regular_bytes(path) for path in root.glob("*.py")}
    files.update({"adapters/" + path.name: regular_bytes(path)
                  for path in (root / "adapters").glob("*.js")})
    return {"version": metadata.version(DISTRIBUTION),
            "digest": digest(canonical(file_hashes(files)))}


class PolicyDrift(SnapshotError):
    """Local authority changed; explicit preparation is required before acceptance."""


def configuration(repo, discover_policies=True):
    repo = consumer_root(repo)
    config = read_json(repo / ".flutter-guidelines.json")
    if (not isinstance(config, dict) or type(config.get("schema")) is not int or
            config["schema"] != 1 or "source" not in config or
            set(config) - {"schema", "source", "policies", "overlays", "cache", "reviewed_guards"}):
        raise SnapshotError("invalid runtime configuration")
    validate_source(config["source"])
    for field in ("policies", "overlays"):
        validate_paths(config.get(field, []))
    reviews = validate_reviews(config.get("reviewed_guards", []))
    if reviews:
        missing = missing_reviews(hook_inventory(repo), reviews)
        if missing:
            raise SnapshotError("; ".join(missing))
    if "cache" in config and (not isinstance(config["cache"], str) or not config["cache"]):
        raise SnapshotError("cache must be a nonempty path string")
    for name in native_policies(repo) if discover_policies else ():
        if name not in config.get("policies", []):
            raise PolicyDrift(f"auto-loaded authority must be listed as policy: {name}")
    return config


def local_files(repo, config):
    return {f"local/{field}/{name}": regular_bytes(repo / name)
            for field in ("policies", "overlays") for name in config.get(field, [])}


def cache_directory(config):
    value = config.get("cache") or os.environ.get("FLUTTER_GUIDELINES_CACHE")
    return checked_path(value or Path.home() / ".cache/flutter-agent-guidelines")


def load_work(repo):
    path = state_root(repo) / "work.json"
    if not path.exists():
        return None
    work = read_json(path)
    if (not isinstance(work, dict) or set(work) != {
            "schema", "id", "consumer", "phase", "source", "revision", "snapshot", "config",
            "local", "controller", "sessions", "update"} or work["schema"] != 1 or
            work["phase"] not in ("active", "closing", "rebaseline-required") or
            not isinstance(work["sessions"], dict)):
        raise SnapshotError("invalid work record; inspect state, never reset silently")
    return work


def verify_work(repo, work, config, verify_local=True):
    require_digest(work["snapshot"])
    if work["consumer"] != str(consumer_root(repo)):
        raise SnapshotError("pinned work belongs to a different consumer worktree")
    if work["source"] != config["source"]:
        raise SnapshotError("source authority mismatch")
    if verify_local and work["config"] != digest(canonical(config)):
        raise SnapshotError("configuration drift during pinned work")
    if work["controller"] != controller_identity():
        raise SnapshotError("installed controller changed during pinned work")
    if verify_local:
        try:
            changed = work["local"] != file_hashes(local_files(repo, config))
        except (OSError, SnapshotError) as error:
            raise PolicyDrift(f"local instruction drift: {error}") from error
        if changed:
            raise PolicyDrift("local instruction drift during pinned work")
    snapshot = state_root(repo) / "snapshots" / work["snapshot"]
    manifest = verify_snapshot(snapshot, work["snapshot"])
    expected = {"consumer": work["consumer"], "source": work["source"], "revision": work["revision"],
                "work": work["id"], "controller": work["controller"]}
    if manifest["metadata"] != expected:
        raise SnapshotError("work provenance mismatch")
    if {name: value for name, value in manifest["files"].items()
            if name.startswith("local/")} != work["local"]:
        raise SnapshotError("local snapshot identity mismatch")
    if regular_bytes(snapshot / "policy-index.json") != canonical(policy_index(work["local"])):
        raise SnapshotError("local scope index mismatch")
    for session in work["sessions"].values():
        if session["snapshot"] != work["snapshot"] or session["work"] != work["id"]:
            raise SnapshotError("session identity mismatch")
    return snapshot


def mark_rebaseline(repo):
    with locked(state_root(repo)):
        work = load_work(repo)
        if work:
            work["phase"] = "rebaseline-required"
            save_json(state_root(repo) / "work.json", work)


def update_check(work):
    try:
        revision = resolve(work["source"])
        return {"state": "CURRENT" if revision == work["revision"] else "UPDATE",
                "revision": revision}
    except (SnapshotError, OSError):
        return {"state": "UNKNOWN", "revision": None}


def context(repo, work, snapshot):
    global_paths = [str(snapshot / entry["snapshot_path"])
                    for entry in policy_index(work["local"])["entries"]
                    if entry["scope"]["kind"] == "global"]
    return ("<!-- flutter-guidelines:context -->\n" + provenance(work, snapshot) + "\n"
            "Resolve shared relative links from Guidelines-Root; focused lookups only.\n"
            f"Consumer-local authority retained. Read global local inputs: {', '.join(global_paths) or 'none'}.\n"
            f"Scoped local index: {snapshot / 'policy-index.json'}. Consult only relevant "
            "cwd/touched-file ancestor policies and applicable native rules. Preserve original "
            "consumer-relative scopes/frontmatter; snapshot paths do not redefine scope. "
            "Do not read unrelated indexed policies globally.\n"
            "Do not edit snapshots/state. Explicit end required; conversations reuse this work.\n\n"
            + regular_bytes(snapshot / "payload/AGENTS.md").decode("utf-8"))


def provenance(work, snapshot):
    return (f"Flutter work {work['id']}; source {work['source']['url']} "
            f"at {work['revision']}; digest {work['snapshot']}.\n"
            f"Verified Guidelines-Root: {snapshot / 'payload'}\n"
            f"Updates: {work['update']['state']} ({work['update']['revision'] or 'unavailable'}); "
            "announce UPDATE/UNKNOWN; pin unchanged.")


def join(repo, runtime, session, role="participant", expected=None, refresh=False,
         adapter=None, lease=None, context_mode="entry"):
    try:
        return _join(repo, runtime, session, role, expected, refresh, adapter, lease, context_mode)
    except PolicyDrift:
        mark_rebaseline(repo)
        raise


def _join(repo, runtime, session, role="participant", expected=None, refresh=False,
         adapter=None, lease=None, context_mode="entry"):
    if context_mode not in ("entry", "provenance", "none"):
        raise SnapshotError("invalid context mode")
    if not isinstance(session, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,300}", session):
        raise SnapshotError("native session identity required")
    if lease is not None and (not isinstance(lease, str) or
                             not re.fullmatch(r"[A-Za-z0-9_.-]{1,300}", lease)):
        raise SnapshotError("invalid session lease")
    root = state_root(repo)
    with locked(root):
        config = configuration(repo)
        work = load_work(repo)
        key = runtime + ":" + session + (":" + lease if lease else "")
        if work is None:
            if expected:
                raise SnapshotError("expected work is no longer active; explicit join cannot prepare")
            revision, _, files = materialize(config["source"], cache_directory(config))
            local = local_files(repo, config)
            identity = uuid.uuid4().hex
            controller = controller_identity()
            snapshots = checked_path(root / "snapshots")
            snapshots.mkdir(exist_ok=True)
            snapshot = write_snapshot(snapshots, {**files, **local,
                "policy-index.json": canonical(policy_index(local))}, {
                "consumer": str(consumer_root(repo)), "source": config["source"], "revision": revision,
                "work": identity, "controller": controller})
            work = {"schema": 1, "id": identity, "consumer": str(consumer_root(repo)), "phase": "active",
                    "source": config["source"], "revision": revision,
                    "snapshot": snapshot.name, "config": digest(canonical(config)),
                    "local": file_hashes(local), "controller": controller,
                    "sessions": {}, "update": {"state": "CURRENT", "revision": revision}}
        snapshot = verify_work(repo, work, config)
        if work["phase"] == "rebaseline-required":
            raise PolicyDrift("rebaseline required before closure/acceptance")
        if expected and expected != work["snapshot"]:
            raise SnapshotError("explicit reviewer digest differs from active work")
        if work["phase"] == "closing" and key not in work["sessions"]:
            raise SnapshotError("work closing; wait for all active sessions to exit")
        previous = work["sessions"].get(key)
        if previous and previous["adapter"] != adapter:
            raise SnapshotError("live adapter changed; exit session before recovery")
        work["sessions"][key] = {"work": work["id"], "snapshot": work["snapshot"],
                                 "role": role, "adapter": adapter, "runtime": runtime,
                                 "session": session, "lease": lease}
        if refresh:
            work["update"] = update_check(work)
        save_json(root / "work.json", work)
        injected = (context(repo, work, snapshot) if context_mode == "entry" else
                    provenance(work, snapshot) if context_mode == "provenance" else "")
        return {"work": work, "root": str(snapshot), "context": injected}


def finalize(root, work):
    if work["phase"] == "closing" and not work["sessions"]:
        history = checked_path(root / "history")
        history.mkdir(exist_ok=True)
        destination = checked_path(history / (work["id"] + ".json"))
        if destination.exists():
            raise SnapshotError("work history collision")
        save_json(destination, work)
        (root / "work.json").unlink()
        return True
    save_json(root / "work.json", work)
    return False


def lifecycle(repo, action, runtime=None, session=None, lease=None):
    root = state_root(repo)
    with locked(root):
        config = configuration(repo, discover_policies=False)
        work = load_work(repo)
        if work is None:
            return {"work": None}
        verify_work(repo, work, config, verify_local=False)
        try:
            configuration(repo)
            verify_work(repo, work, config)
        except PolicyDrift:
            work["phase"] = "rebaseline-required"
            save_json(root / "work.json", work)
        if action == "end" and work["phase"] == "rebaseline-required":
            raise PolicyDrift("rebaseline required before closure/acceptance")
        if action == "refresh-check":
            work["update"] = update_check(work)
        elif action == "end":
            work["phase"] = "closing"
        elif action == "release":
            for key, receipt in tuple(work["sessions"].items()):
                if (receipt["runtime"] == runtime and receipt["session"] == session and
                        (lease is None or receipt["lease"] == lease)):
                    del work["sessions"][key]
        closed = finalize(root, work)
        return {"work": work, "closed": closed}


def rebaseline(repo, apply=False):
    """Human-owned replacement preparation; keep the existing common-source revision."""
    from .installation import conflicts
    root = state_root(repo)
    with locked(root):
        config = configuration(repo, discover_policies=False)
        work = load_work(repo)
        if work is None:
            raise SnapshotError("rebaseline requires existing work")
        snapshot = verify_work(repo, work, config, verify_local=False)
        if work["sessions"]:
            raise SnapshotError("exit all sessions and release their leases before rebaseline")
        findings = conflicts(repo)
        if findings:
            raise SnapshotError("competing/external loader requires inventory: " + ", ".join(findings))
        config["policies"] = sorted(set(config.get("policies", [])) | set(native_policies(repo)))
        local = local_files(repo, config)
        result = {"apply": apply, "previous": work["snapshot"], "revision": work["revision"],
                  "policies": config["policies"]}
        if not apply:
            return result
        manifest = verify_snapshot(snapshot, work["snapshot"])
        files = {name: regular_bytes(snapshot / name) for name in manifest["files"]
                 if not name.startswith("local/") and name != "policy-index.json"}
        identity = uuid.uuid4().hex
        replacement = write_snapshot(root / "snapshots", {**files, **local,
            "policy-index.json": canonical(policy_index(local))}, {
            "consumer": work["consumer"], "source": work["source"], "revision": work["revision"],
            "work": identity, "controller": work["controller"]})
        history = checked_path(root / "history")
        history.mkdir(exist_ok=True)
        destination = checked_path(history / (work["id"] + ".json"))
        if destination.exists():
            raise SnapshotError("work history collision")
        save_json(destination, work | {"phase": "rebaseline-required"})
        save_json(repo / ".flutter-guidelines.json", config)
        renewed = work | {"id": identity, "phase": "active", "snapshot": replacement.name,
                          "local": file_hashes(local), "config": digest(canonical(config))}
        save_json(root / "work.json", renewed)
        return result | {"work": renewed}
