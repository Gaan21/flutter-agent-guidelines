"""Opt-in profiles are portable project choices, not package defaults."""

from importlib import resources
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from flutter_agent_guidelines import installed
from flutter_agent_guidelines import installed_installation as connection
from flutter_agent_guidelines.runtime_io import save_json
from flutter_agent_guidelines.snapshots import SnapshotError, canonical, digest


class InstalledProfileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="installed-profiles-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "consumer"
        self.repo.mkdir()
        environment = patch.dict(os.environ, {
            "HOME": str(self.root / "home"),
            "CLAUDE_CONFIG_DIR": str(self.root / "home/.claude"),
            "XDG_CONFIG_HOME": str(self.root / "home/config")})
        environment.start()
        self.addCleanup(environment.stop)
        for key in ("OPENCODE_CONFIG", "OPENCODE_CONFIG_CONTENT", "OPENCODE_PURE",
                    "OPENCODE_DISABLE_PROJECT_CONFIG", "CLAUDE_CODE_SIMPLE", "CLAUDE_CODE_SAFE_MODE"):
            os.environ.pop(key, None)

    def cli(self, *args, payload=None):
        return subprocess.run([sys.executable, "-I", "-m", "flutter_agent_guidelines.cli", *args],
                              input=json.dumps(payload) if payload is not None else None,
                              capture_output=True, text=True, cwd=self.root)

    def connect(self, profiles=None):
        installed.configure(self.repo, apply=True, profiles=profiles)
        connection.install(self.repo, "opencode", apply=True)

    def test_generic_default_does_not_activate_architecture(self):
        self.connect()
        status = installed.status(self.repo)
        self.assertEqual(status["pin"]["profiles"], [])
        text = installed.context(self.repo)
        self.assertIn("Selected profiles: none (generic guidance)", text)
        self.assertNotIn("Selected profile: architecture", text)

    def test_claude_prompt_keeps_identity_and_profile_pointer_without_entry(self):
        installed.configure(self.repo, apply=True, profiles=["architecture"])
        connection.install(self.repo, "claude", apply=True)
        expected = installed.status(self.repo)["identity"]
        entry = resources.files("flutter_agent_guidelines").joinpath("payload/AGENTS.md").read_text()
        for event in ("SessionStart", "UserPromptSubmit"):
            response = self.cli("installed-hook", "--runtime", "claude", payload={
                "cwd": str(self.repo), "hook_event_name": event, "expected": expected})
            text = json.loads(response.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn(expected, text)
            self.assertIn("Selected profile: architecture (profiles/architecture.md", text)
            self.assertIn("must be consulted before implementation when applicable", text)
            if event == "SessionStart":
                self.assertIn(entry, text)
            else:
                self.assertNotIn(entry.strip(), text)
                self.assertLess(len(text), len(entry))

    def test_cli_opt_in_preview_connection_and_focused_pointer(self):
        args = ("configure", "--installed", "--repo", str(self.repo), "--profile", "architecture")
        preview = self.cli(*args)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(list(self.repo.iterdir()), [])
        generic = installed.identity()
        choice = json.loads(preview.stdout)["pin"]
        self.assertEqual(choice["profiles"], ["architecture"])
        self.assertNotEqual(choice, generic)
        self.assertEqual(choice["payload"], generic["payload"])
        self.assertEqual(choice["bundle"], generic["bundle"])
        applied = self.cli(*args, "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        before = set(self.repo.rglob("*"))
        plan = connection.install(self.repo, "opencode")
        self.assertFalse(plan["apply"])
        self.assertEqual(set(self.repo.rglob("*")), before)
        connection.install(self.repo, "opencode", apply=True)
        text = installed.context(self.repo)
        self.assertIn("Selected profile: architecture (profiles/architecture.md", text)
        self.assertIn("must be consulted before implementation when applicable", text)
        profile = resources.files("flutter_agent_guidelines").joinpath(
            "payload/profiles/architecture.md").read_text()
        self.assertNotIn(profile.strip(), text)
        entry = resources.files("flutter_agent_guidelines").joinpath("payload/AGENTS.md").read_text()
        self.assertIn(entry, text)

    def test_same_profile_identity_on_second_machine_and_expected_mismatch(self):
        self.connect(["architecture"])
        selected = installed.status(self.repo)
        other = self.root / "reviewer"
        other.mkdir()
        shutil.copyfile(self.repo / installed.PIN, other / installed.PIN)
        connection.install(other, "opencode", apply=True)
        self.assertEqual(installed.status(other, selected["identity"])["pin"], selected["pin"])
        different = installed.pin(other)
        different["profiles"] = []
        save_json(other / installed.PIN, different)
        with self.assertRaisesRegex(SnapshotError, "independently retained"):
            installed.context(other, selected["identity"])
        result = self.cli("doctor", "--repo", str(other), "--expected", selected["identity"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("independently retained", result.stderr)

    def test_selection_preserved_until_explicit_upgrade_and_clear(self):
        self.connect(["architecture"])
        selected = installed.status(self.repo)
        configured = installed.configure(self.repo)
        self.assertEqual(configured["pin"], selected["pin"])
        with self.assertRaisesRegex(SnapshotError, "upgrade-installed"):
            installed.configure(self.repo, apply=True, profiles=[])
        path = installed.root(self.repo) / selected["pin"]["bundle"]
        before = {str(item.relative_to(path)): item.read_bytes() for item in path.rglob("*")
                  if item.is_file()}
        snapshot_tree = set(self.repo.rglob("*"))
        preserved = installed.upgrade(self.repo)
        self.assertEqual(preserved["after"]["profiles"], ["architecture"])
        preview = self.cli("upgrade-installed", "--repo", str(self.repo), "--clear-profiles")
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(set(self.repo.rglob("*")), snapshot_tree)
        self.assertEqual(installed.pin(self.repo), selected["pin"])
        cleared = self.cli("upgrade-installed", "--repo", str(self.repo), "--clear-profiles", "--apply")
        self.assertEqual(cleared.returncode, 0, cleared.stderr)
        self.assertEqual(installed.pin(self.repo)["profiles"], [])
        self.assertNotEqual(installed.status(self.repo)["identity"], selected["identity"])
        self.assertEqual(before, {str(item.relative_to(path)): item.read_bytes()
                                 for item in path.rglob("*") if item.is_file()})
        chosen = self.cli("upgrade-installed", "--repo", str(self.repo), "--profile", "architecture", "--apply")
        self.assertEqual(chosen.returncode, 0, chosen.stderr)
        self.assertEqual(installed.pin(self.repo)["profiles"], ["architecture"])

    def test_initial_schema_without_profiles_stays_generic_and_verifiable(self):
        self.connect()
        old = installed.pin(self.repo)
        old.pop("profiles")
        save_json(self.repo / installed.PIN, old)
        expected = digest(canonical(old))
        self.assertEqual(installed.status(self.repo, expected)["identity"], expected)
        self.assertIn("none (generic guidance)", installed.context(self.repo, expected))
        self.assertEqual(installed.configure(self.repo, apply=True)["identity"], expected)
        self.assertNotIn("profiles", installed.pin(self.repo))
        installed.upgrade(self.repo, apply=True)
        self.assertEqual(installed.pin(self.repo)["profiles"], [])

    def test_malformed_and_unknown_selection_is_rejected_without_export(self):
        for invalid in (None, "architecture", True, {}, [None], ["unknown"],
                        ["../architecture"], ["architecture", "architecture"]):
            with self.subTest(invalid=invalid):
                value = installed.identity()
                value["profiles"] = invalid
                save_json(self.repo / installed.PIN, value)
                with patch("flutter_agent_guidelines.installed.export_bundle",
                           side_effect=AssertionError("invalid selection must not be exported")):
                    with self.assertRaisesRegex(SnapshotError, "profiles"):
                        connection.install(self.repo, "opencode", apply=True)
        (self.repo / installed.PIN).unlink()
        for invalid in (["unknown"], ["architecture", "architecture"], "architecture"):
            with self.assertRaisesRegex(SnapshotError, "profiles"):
                installed.configure(self.repo, profiles=invalid, apply=True)
        self.assertFalse((self.repo / installed.PIN).exists())

    def test_package_mismatch_is_checked_before_materialization(self):
        choice = installed.identity(["architecture"])
        choice["controller"] = "0" * 64
        save_json(self.repo / installed.PIN, choice)
        with patch("flutter_agent_guidelines.installed.export_bundle",
                   side_effect=AssertionError("mismatch must not be exported")):
            with self.assertRaisesRegex(SnapshotError, "differs from project pin"):
                connection.install(self.repo, "opencode", apply=True)
        self.assertEqual(installed.pin(self.repo), choice)

    def test_missing_profile_resource_cannot_be_selected(self):
        files = installed.package_files()
        files.pop("payload/profiles/architecture.md", None)
        with patch("flutter_agent_guidelines.installed.package_files", return_value=files):
            with self.assertRaisesRegex(SnapshotError, "missing from installed payload"):
                installed.configure(self.repo, profiles=["architecture"])
        self.assertEqual(list(self.repo.iterdir()), [])

    def test_cli_invalid_profile_and_legacy_options_have_actionable_errors(self):
        help_result = self.cli("configure", "--help")
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--profile {architecture}", help_result.stdout)
        for args, message in (
                (("--installed", "--profile", "unknown"), "invalid choice"),
                (("--profile", "architecture"), "requires configure --installed"),
                (("--source-url", "https://example.invalid/guidance.git"), "both legacy"),
                (("--installed", "--source-url", "https://example.invalid/guidance.git"), "cannot be combined"),
                (("--installed", "--profile", "architecture", "--clear-profiles"), "not allowed")):
            with self.subTest(args=args):
                result = self.cli("configure", "--repo", str(self.repo), *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertEqual(list(self.repo.iterdir()), [])
