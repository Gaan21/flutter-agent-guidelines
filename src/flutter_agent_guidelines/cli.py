"""Content operations and explicitly installed local runtime integration."""

import argparse
import json
import os
import sys
from pathlib import Path

from .bundles import export_bundle, inspect_package
from .snapshots import SnapshotError, verify_snapshot
from . import installation, runtime
from .adapters import hook
from .runtime_io import consumer_root
from .hook_reviews import hook_inventory


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect and verify Flutter guidance snapshots")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect", help="show installed content identity; no approval claim")
    export = commands.add_parser("export", help="export into an existing parent/digest directory")
    export.add_argument("parent")
    verify = commands.add_parser("verify", help="offline integrity verification; not source authentication")
    verify.add_argument("snapshot")
    verify.add_argument("--digest", help="independently retained expected manifest SHA-256")
    for name in ("configure", "install", "uninstall", "status", "refresh-check", "end", "release", "doctor", "join",
                 "inventory-hooks", "review-guard", "rebaseline", "track"):
        command = commands.add_parser(name)
        command.add_argument("--repo", required=True, type=Path)
        if name in ("configure", "install", "uninstall", "review-guard", "rebaseline", "track"):
            command.add_argument("--apply", action="store_true")
        if name == "configure":
            command.add_argument("--source-url", required=True)
            command.add_argument("--source-ref", required=True)
            command.add_argument("--policy", action="append", default=[])
            command.add_argument("--overlay", action="append", default=[])
            command.add_argument("--cache")
            command.add_argument("--auto-update", action="store_true",
                                 help="approve future executable controllers from this source")
        if name == "track":
            command.add_argument("--source-ref", required=True)
        if name == "install":
            command.add_argument("--runtime", choices=("claude", "opencode", "both"), default="both")
        if name in ("release", "join"):
            command.add_argument("--runtime", required=True, choices=("claude", "opencode"))
            command.add_argument("--session", required=True)
        if name == "join":
            command.add_argument("--role", default="reviewer")
            command.add_argument("--expected", required=True)
        if name == "review-guard":
            command.add_argument("--source", required=True)
            command.add_argument("--digest", required=True)
            command.add_argument("--non-instruction-guard", action="store_true")
    for name in ("hook", "bridge"):
        adapter = commands.add_parser(name)
        adapter.add_argument("--runtime", required=True, choices=("claude", "opencode"))
    arguments = parser.parse_args(argv)
    try:
        if hasattr(arguments, "repo"):
            arguments.repo = consumer_root(arguments.repo)
        if arguments.command == "bridge":
            from .bootstrap import hook as bridge
            return bridge(arguments.runtime)
        lifecycle_command = arguments.command in (
            "status", "refresh-check", "end", "release", "join", "rebaseline")
        if lifecycle_command and not os.environ.get("FLUTTER_GUIDELINES_DEPLOYMENT"):
            from . import bootstrap
            if bootstrap.enabled(arguments.repo):
                result = bootstrap.command(arguments.repo, list(argv if argv is not None else sys.argv[1:]))
                print(json.dumps(result, sort_keys=True, indent=2))
                return 0
        if arguments.command == "track":
            from .bootstrap import track
            result = track(arguments.repo, arguments.source_ref, arguments.apply)
        elif arguments.command == "hook":
            return hook(arguments.runtime)
        elif arguments.command == "configure":
            result = installation.configure(arguments.repo, {"url": arguments.source_url,
                "ref": arguments.source_ref}, arguments.policy, arguments.overlay,
                 arguments.cache, arguments.apply, arguments.auto_update)
        elif arguments.command == "install":
            result = installation.install(arguments.repo, arguments.runtime, arguments.apply)
        elif arguments.command == "uninstall":
            result = installation.uninstall(arguments.repo, arguments.apply)
        elif arguments.command == "doctor":
            result = installation.doctor(arguments.repo)
        elif arguments.command == "inventory-hooks":
            result = {"hooks": hook_inventory(arguments.repo)}
        elif arguments.command == "review-guard":
            result = installation.review_guard(arguments.repo, arguments.source, arguments.digest,
                                                arguments.non_instruction_guard, arguments.apply)
        elif arguments.command == "join":
            result = runtime.join(arguments.repo, arguments.runtime, arguments.session,
                                  arguments.role, arguments.expected)
        elif arguments.command == "rebaseline":
            result = runtime.rebaseline(arguments.repo, arguments.apply)
        elif arguments.command in ("status", "refresh-check", "end", "release"):
            result = runtime.lifecycle(arguments.repo, arguments.command,
                getattr(arguments, "runtime", None), getattr(arguments, "session", None))
        elif arguments.command == "inspect":
            result = inspect_package()
        elif arguments.command == "export":
            path = export_bundle(arguments.parent)
            result = {"snapshot": str(path), "digest": path.name, "approved": False}
        else:
            result = {"integrity": "verified", "manifest": verify_snapshot(
                arguments.snapshot, arguments.digest)}
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (SnapshotError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"flutter-guidelines: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
