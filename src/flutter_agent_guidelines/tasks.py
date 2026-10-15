"""Limited task-pin API. Trust decisions belong to the calling operator.

No launcher, session lock, finish operation, source resolver or signature verifier.
Role joins return receipts; the caller retains them outside the immutable snapshot.
"""

import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

from .bundles import inspect_package
from .snapshots import (
    SnapshotError, canonical, checked_path, digest, file_hashes, regular_bytes,
    relative_name, require_digest, verify_snapshot, write_snapshot,
)

TASK_SLOT = ".flutter-guidelines-task"


def approved_source(record_bytes, approved_record_sha256, bundle, manifest):
    """Validate an externally approved record, NOT its publisher authenticity.

    Caller must authenticate source/artifact and approve the exact record digest
    out of band. A digest obtained from the same untrusted record is not approval.
    """
    if digest(record_bytes) != require_digest(approved_record_sha256):
        raise SnapshotError("release record differs from operator-approved digest")
    try:
        record = json.loads(record_bytes)
        required = {"schema", "approved", "authority", "approval_reference", "source_url",
                    "source_sha", "version", "artifact_sha256", "bundle_digest",
                    "payload_digest"}
        if (set(record) != required or type(record["schema"]) is not int
                or record["schema"] != 1 or record["approved"] is not True):
            raise SnapshotError("unapproved or invalid release record")
        for field in ("authority", "approval_reference"):
            if not isinstance(record[field], str) or not record[field].strip():
                raise SnapshotError("missing approval authority/reference")
        if not isinstance(record["source_url"], str):
            raise SnapshotError("expected source URL text")
        try:
            source = urlsplit(record["source_url"])
        except ValueError as error:
            raise SnapshotError("invalid source URL") from error
        if source.scheme != "https" or not source.hostname or source.username or source.password:
            raise SnapshotError("expected public HTTPS source URL without credentials")
        if not re.fullmatch(r"[0-9a-f]{40}", record["source_sha"]):
            raise SnapshotError("expected full 40-character source Git SHA")
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", record["version"]):
            raise SnapshotError("only stable approved releases can prepare tasks")
        require_digest(record["artifact_sha256"])
        current = inspect_package()
        current_files = current.pop("files")
        if current["development"]:
            raise SnapshotError("development installation cannot prepare operational tasks")
        if manifest["metadata"] != current or manifest["files"] != current_files:
            raise SnapshotError("bundle differs from installed package")
        if (record["version"] != current["version"] or
                record["bundle_digest"] != bundle.name or
                record["payload_digest"] != current["payload_digest"]):
            raise SnapshotError("release record does not match package payload/bundle")
    except (TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SnapshotError("invalid release record") from error
    return record


def local_files(root, names):
    if not isinstance(names, (list, tuple)) or len(set(names)) != len(names):
        raise SnapshotError("explicit unique local file list required")
    result = {}
    for name in names:
        relative = relative_name(name)
        if relative.parts[0] == TASK_SLOT:
            raise SnapshotError("task state cannot be a policy input")
        result[name] = regular_bytes(root / name)
    return result


def prepare_task(*, consumer_root, task_id, bundle, release_record,
                 approved_record_sha256, policy_paths, overlay_paths, context):
    """Create one exclusive task slot per explicit consumer/worktree root.

    Context must supply external_contract_pins, toolchain_configuration and
    preloads. Values are caller-verified JSON evidence, never commands to run.
    All authoritative policy/overlay files must be listed by the caller.
    """
    if not isinstance(task_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", task_id):
        raise SnapshotError("invalid task ID")
    root = checked_path(consumer_root)
    if not root.is_dir() or not Path(consumer_root).is_absolute():
        raise SnapshotError("explicit absolute consumer directory required")
    bundle = checked_path(bundle)
    manifest = verify_snapshot(bundle)
    record = approved_source(release_record, approved_record_sha256, bundle, manifest)
    if not isinstance(context, dict) or set(context) != {
            "external_contract_pins", "toolchain_configuration", "preloads"}:
        raise SnapshotError("explicit contract/toolchain/preload context required")
    policies = local_files(root, policy_paths)
    overlays = local_files(root, overlay_paths)
    if not policies:
        raise SnapshotError("at least one consumer policy required")
    files = {}
    for name, expected in manifest["files"].items():
        content = regular_bytes(bundle / name)
        if digest(content) != expected:
            raise SnapshotError("bundle changed while preparing task")
        files[f"common/{name}"] = content
    common_manifest = regular_bytes(bundle / "manifest.json")
    if digest(common_manifest) != bundle.name:
        raise SnapshotError("bundle manifest changed while preparing task")
    files["common/manifest.json"] = common_manifest
    files.update({f"policy/{name}": value for name, value in policies.items()})
    files.update({f"overlay/{name}": value for name, value in overlays.items()})
    files["release-record.json"] = release_record
    identity = {
        "kind": "task-pin", "task_id": task_id, "consumer_root": str(root),
        "source": record, "approved_record_sha256": approved_record_sha256,
        "bundle_digest": bundle.name,
        "policy_digest": digest(canonical(file_hashes(policies))),
        "overlay_digest": digest(canonical(file_hashes(overlays))),
        "context": context,
    }
    # Validate serializability before reserving the live slot.
    canonical(identity)
    slot = checked_path(root / TASK_SLOT)
    try:
        slot.mkdir()
    except FileExistsError as error:
        raise SnapshotError("consumer already has a task slot; never overwrite live tasks") from error
    try:
        return write_snapshot(slot, files, identity)
    except BaseException:
        shutil.rmtree(slot)
        raise


def join_task(snapshot, *, consumer_root, expected_digest, role):
    """Offline join of an exact pin, returning an immutable-identity receipt.

    No reread of mutable consumer policy or installed package; upgrades cannot
    replace this task's content. Preserve the receipt externally for review.
    """
    if role not in ("implementer", "reviewer"):
        raise SnapshotError("role must be implementer or reviewer")
    root = checked_path(consumer_root)
    if not Path(consumer_root).is_absolute() or not root.is_dir():
        raise SnapshotError("explicit absolute consumer directory required")
    snapshot = checked_path(snapshot)
    manifest = verify_snapshot(snapshot, require_digest(expected_digest))
    identity = manifest["metadata"]
    if (identity.get("kind") != "task-pin" or identity.get("consumer_root") != str(root)
            or snapshot.parent != root / TASK_SLOT):
        raise SnapshotError("task/consumer identity mismatch")
    return {key: identity[key] for key in (
        "task_id", "consumer_root", "bundle_digest", "policy_digest", "overlay_digest"
    )} | {"role": role, "task_digest": expected_digest,
         "source_sha": identity["source"]["source_sha"]}
