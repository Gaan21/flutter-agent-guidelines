"""Explicit resource operations only; no launcher or command executor."""

import argparse
import json
import sys

from .bundles import export_bundle, inspect_package
from .snapshots import SnapshotError, verify_snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect and verify Flutter guidance snapshots")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect", help="show installed content identity; no approval claim")
    export = commands.add_parser("export", help="export into an existing parent/digest directory")
    export.add_argument("parent")
    verify = commands.add_parser("verify", help="offline integrity verification; not source authentication")
    verify.add_argument("snapshot")
    verify.add_argument("--digest", help="independently retained expected manifest SHA-256")
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "inspect":
            result = inspect_package()
        elif arguments.command == "export":
            path = export_bundle(arguments.parent)
            result = {"snapshot": str(path), "digest": path.name, "approved": False}
        else:
            result = {"integrity": "verified", "manifest": verify_snapshot(
                arguments.snapshot, arguments.digest)}
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (SnapshotError, OSError, ValueError) as error:
        print(f"flutter-guidelines: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
