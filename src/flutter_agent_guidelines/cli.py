"""Content operations and explicitly installed local runtime integration."""

import argparse
import json
import os
import sys
from pathlib import Path

from .bundles import export_bundle, inspect_package
from .snapshots import SnapshotError, verify_snapshot
from . import installation, runtime, installed, installed_installation
from .adapters import hook
from .runtime_io import consumer_root
from .hook_reviews import hook_inventory


def main(argv=None):
    parser = argparse.ArgumentParser(description="Connect installed Flutter guidance and verify exact identities")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect", help="show installed content identity; no approval claim")
    export = commands.add_parser("export", help="export into an existing parent/digest directory")
    export.add_argument("parent")
    verify = commands.add_parser("verify", help="offline integrity verification; not source authentication")
    verify.add_argument("snapshot")
    verify.add_argument("--digest", help="independently retained expected manifest SHA-256")
    for name in ("configure", "install", "uninstall", "status", "refresh-check", "end", "release", "doctor", "join",
                 "inventory-hooks", "review-guard", "rebaseline", "track", "upgrade-installed"):
        command = commands.add_parser(name)
        command.add_argument("--repo", required=True, type=Path)
        if name in ("configure", "install", "uninstall", "review-guard", "rebaseline", "track", "upgrade-installed"):
            command.add_argument("--apply", action="store_true")
        if name in ("configure", "upgrade-installed"):
            selection = command.add_mutually_exclusive_group()
            selection.add_argument("--profile", action="append", choices=tuple(installed.PROFILES),
                                   help="opt in to a project profile; configure requires --installed")
            selection.add_argument("--clear-profiles", action="store_true",
                                   help="explicitly select generic guidance without a profile")
            lint = command.add_mutually_exclusive_group()
            lint.add_argument("--lint-contract", type=Path,
                              help="record an exported architecture lint contract; configure requires --installed")
            lint.add_argument("--clear-lint-contract", action="store_true",
                              help="explicitly remove the recorded lint pair")
        if name == "configure":
            command.add_argument("--installed", action="store_true",
                                 help="pin this installed package; no Git source or work lifecycle")
            command.add_argument("--source-url", help="legacy Git source; requires --source-ref, excludes --installed")
            command.add_argument("--source-ref", help="legacy Git ref; requires --source-url, excludes --installed")
            command.add_argument("--policy", action="append", default=[])
            command.add_argument("--overlay", action="append", default=[])
            command.add_argument("--cache")
            command.add_argument("--auto-update", action="store_true",
                                 help="approve future executable controllers from this source")
        if name == "track":
            command.add_argument("--source-ref", required=True)
        if name in ("status", "doctor"):
            command.add_argument("--expected", help="independently retained installed project identity SHA-256")
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
    for name in ("hook", "bridge", "installed-hook"):
        adapter = commands.add_parser(name)
        adapter.add_argument("--runtime", required=True, choices=("claude", "opencode"))
    arguments = parser.parse_args(argv)
    try:
        if hasattr(arguments, "repo"):
            arguments.repo = consumer_root(arguments.repo)
        if arguments.command == "installed-hook":
            return installed.hook(arguments.runtime)
        simple = hasattr(arguments, "repo") and (installed.enabled(arguments.repo) or
            installed_installation.record_path(arguments.repo).exists())
        if getattr(arguments, "expected", None) and arguments.command in ("status", "doctor") and not simple:
            raise SnapshotError("--expected on status/doctor requires installed mode")
        if (arguments.command == "configure" and not arguments.installed and
                (arguments.profile is not None or arguments.clear_profiles)):
            raise SnapshotError("profile selection requires configure --installed")
        if (arguments.command == "configure" and not arguments.installed and
                (arguments.lint_contract is not None or arguments.clear_lint_contract)):
            raise SnapshotError("lint contract selection requires configure --installed")
        if arguments.command == "configure" and arguments.installed:
            if (arguments.source_url or arguments.source_ref or arguments.auto_update or
                    arguments.policy or arguments.overlay or arguments.cache):
                raise SnapshotError("--installed cannot be combined with legacy source/policy options")
            result = installed.configure(arguments.repo, arguments.apply,
                [] if arguments.clear_profiles else arguments.profile,
                arguments.lint_contract, arguments.clear_lint_contract)
        elif arguments.command == "upgrade-installed":
            result = installed.upgrade(arguments.repo, arguments.apply,
                [] if arguments.clear_profiles else arguments.profile,
                arguments.lint_contract, arguments.clear_lint_contract)
        elif simple and arguments.command in ("install", "uninstall", "status", "doctor", "refresh-check"):
            if arguments.command == "install":
                result = installed_installation.install(arguments.repo, arguments.runtime, arguments.apply)
            elif arguments.command == "uninstall":
                result = installed_installation.uninstall(arguments.repo, arguments.apply)
            else:
                result = installed.status(arguments.repo, getattr(arguments, "expected", None))
        elif simple and arguments.command in ("end", "release", "join", "rebaseline", "track", "review-guard", "configure"):
            raise SnapshotError("installed mode has no work lifecycle or legacy configuration; "
                                "use status or upgrade-installed")
        else:
            result = None
        if result is not None:
            print(json.dumps(result, sort_keys=True, indent=2))
            return 0
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
            if not arguments.source_url or not arguments.source_ref:
                raise SnapshotError("choose --installed (recommended) or supply both legacy --source-url and --source-ref")
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
