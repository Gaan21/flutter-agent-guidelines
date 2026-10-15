"""Exact owner-reviewed non-instruction guard definitions; no behavior inference."""

import os
from pathlib import Path

from .runtime_io import read_json
from .snapshots import SnapshotError, canonical, checked_path, digest, require_digest

REVIEW_PURPOSE = "non-instruction-guard"
INVENTORY_EVENTS = ("SessionStart", "UserPromptSubmit", "PreToolUse")


def validate_reviews(reviews):
    if not isinstance(reviews, list):
        raise SnapshotError("reviewed_guards must be a list")
    seen = set()
    for review in reviews:
        if (not isinstance(review, dict) or set(review) != {"source", "event", "digest", "purpose"}
                or not isinstance(review["source"], str) or not review["source"]
                or review["event"] != "PreToolUse" or review["purpose"] != REVIEW_PURPOSE):
            raise SnapshotError("only exact reviewed non-instruction PreToolUse guards are approvable")
        require_digest(review["digest"])
        key = review_key(review)
        if key in seen:
            raise SnapshotError("duplicate reviewed guard")
        seen.add(key)
    return reviews


def review_key(value):
    return value["source"], value["event"], value["digest"]


def settings_sources(repo):
    paths = [(name, repo / name) for name in (".claude/settings.json", ".claude/settings.local.json")]
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    path = checked_path(home / "settings.json")
    paths.append((str(path), path))
    return [(label, checked_path(path)) for label, path in paths]


def hook_inventory(repo):
    result = []
    for source, path in settings_sources(repo):
        if not path.exists():
            continue
        settings = read_json(path)
        if not isinstance(settings, dict) or not isinstance(settings.get("hooks", {}), dict):
            raise SnapshotError(f"invalid hook settings: {source}")
        for event in INVENTORY_EVENTS:
            groups = settings.get("hooks", {}).get(event, [])
            if not isinstance(groups, list):
                raise SnapshotError(f"invalid hook groups: {source}:{event}")
            for group in groups:
                if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                    raise SnapshotError(f"invalid hook group: {source}:{event}")
                selector = {key: value for key, value in group.items() if key != "hooks"}
                for handler in group["hooks"]:
                    if not isinstance(handler, dict):
                        raise SnapshotError(f"invalid handler: {source}:{event}")
                    fingerprint = digest(canonical({"selector": selector, "handler": handler}))
                    result.append({"source": source, "event": event, "digest": fingerprint,
                                   "selector": selector, "handler": handler,
                                   "approvable": event == "PreToolUse" and
                                   handler.get("type") in ("command", "http")})
    return result


def guard_approved(item, reviews):
    return item["approvable"] and any(review_key(item) == review_key(review) for review in reviews)


def missing_reviews(inventory, reviews):
    present = {review_key(item) for item in inventory if item["approvable"]}
    return [f"reviewed guard missing/changed: {review['source']}:{review['event']} "
            f"sha256={review['digest']}" for review in reviews if review_key(review) not in present]
