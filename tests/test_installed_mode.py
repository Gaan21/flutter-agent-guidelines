"""Installed delivery: portable pins, no lifecycle, and real subprocess adapters."""

from importlib import resources
import io
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
from flutter_agent_guidelines.runtime_io import read_json, save_json
from flutter_agent_guidelines.snapshots import SnapshotError


class InstalledTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="installed-guidance-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "project with spaces"
        self.repo.mkdir()
        env = patch.dict(os.environ, {"HOME": str(self.root / "home"),
            "CLAUDE_CONFIG_DIR": str(self.root / "home/.claude"),
            "XDG_CONFIG_HOME": str(self.root / "home/config")})
        env.start()
        self.addCleanup(env.stop)
        for key in ("OPENCODE_CONFIG", "OPENCODE_CONFIG_CONTENT", "OPENCODE_PURE",
                    "OPENCODE_DISABLE_PROJECT_CONFIG", "CLAUDE_CODE_SIMPLE", "CLAUDE_CODE_SAFE_MODE"):
            os.environ.pop(key, None)

    def cli(self, *args, payload=None):
        return subprocess.run([sys.executable, "-I", "-m", "flutter_agent_guidelines.cli", *args],
            input=json.dumps(payload) if payload is not None else None, capture_output=True,
            text=True, cwd=self.root)

    def configure(self, runtime="both"):
        installed.configure(self.repo, apply=True)
        connection.install(self.repo, runtime, apply=True)

    def test_preview_and_cli_connection(self):
        before = set(self.repo.iterdir())
        preview = self.cli("configure", "--installed", "--repo", str(self.repo))
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(set(self.repo.iterdir()), before)
        saved = self.cli("configure", "--installed", "--repo", str(self.repo), "--apply")
        self.assertEqual(saved.returncode, 0, saved.stderr)
        self.assertEqual(json.loads(saved.stdout)["identity"], json.loads(preview.stdout)["identity"])
        install = self.cli("install", "--repo", str(self.repo), "--apply")
        self.assertEqual(install.returncode, 0, install.stderr)
        status = self.cli("doctor", "--repo", str(self.repo))
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["installation"], "verified")
        ignore = (self.repo / ".gitignore").read_text().splitlines()
        self.assertNotIn("/" + installed.PIN, ignore)

    def test_portable_pin_recreated_on_other_machine(self):
        self.configure()
        expected = installed.status(self.repo)["identity"]
        other = self.root / "other-machine"
        other.mkdir()
        shutil.copyfile(self.repo / installed.PIN, other / installed.PIN)
        before = set(other.iterdir())
        connection.install(other, "opencode")
        self.assertEqual(set(other.iterdir()), before)
        connection.install(other, "opencode", apply=True)
        self.assertEqual(installed.status(other, expected)["identity"], expected)
        with self.assertRaisesRegex(SnapshotError, "independently retained"):
            installed.status(other, "0" * 64)

    def test_local_policy_and_guard_changes_do_not_change_identity(self):
        self.configure()
        expected = installed.status(self.repo)["identity"]
        (self.repo / "AGENTS.md").write_text("New native instructions")
        (self.repo / "CLAUDE.md").write_text("Native import @AGENTS.md")
        value = connection.settings(self.repo)
        value["permissions"] = {"deny": ["Read(secret)"]}
        value["hooks"]["PreToolUse"] = [{"hooks": [{"type": "command", "command": "guard-v1"}]}]
        save_json(self.repo / connection.SETTINGS, value)
        self.assertEqual(installed.status(self.repo)["identity"], expected)
        value["hooks"].pop("PreToolUse")
        save_json(self.repo / connection.SETTINGS, value)
        self.assertEqual(installed.status(self.repo)["identity"], expected)
        self.assertNotIn("New native instructions", installed.context(self.repo))
        self.assertFalse((self.repo / ".flutter-guidelines").exists())

    def test_all_simple_operations_are_offline_without_product_commands(self):
        with patch("subprocess.run", side_effect=AssertionError("no executable may be launched")):
            self.configure()
            expected = installed.status(self.repo)["identity"]
            self.assertIn(expected, installed.context(self.repo))
            installed.upgrade(self.repo, apply=True)
            connection.uninstall(self.repo, apply=True)

    def test_mismatch_is_visible_without_repinning(self):
        self.configure()
        selected = installed.pin(self.repo)
        selected["controller"] = "0" * 64
        save_json(self.repo / installed.PIN, selected)
        before = (self.repo / installed.PIN).read_bytes()
        result = self.cli("status", "--repo", str(self.repo))
        self.assertEqual(result.returncode, 1)
        self.assertIn("differs from project pin", result.stderr)
        with self.assertRaisesRegex(SnapshotError, "upgrade-installed"):
            installed.configure(self.repo, apply=True)
        warning = self.cli("installed-hook", "--runtime", "claude", payload={
            "cwd": str(self.repo), "hook_event_name": "SessionStart"})
        self.assertIn("no context injected", json.loads(warning.stdout)["systemMessage"])
        self.assertEqual((self.repo / installed.PIN).read_bytes(), before)

    def test_explicit_upgrade_preview_apply_and_connection_refresh(self):
        self.configure()
        old = installed.pin(self.repo)
        old["controller"] = "a" * 64
        save_json(self.repo / installed.PIN, old)
        old_settings = (self.repo / connection.SETTINGS).read_bytes()
        preview = installed.upgrade(self.repo)
        self.assertEqual(installed.pin(self.repo), old)
        self.assertEqual((self.repo / connection.SETTINGS).read_bytes(), old_settings)
        self.assertNotEqual(preview["before"], preview["after"])
        result = self.cli("upgrade-installed", "--repo", str(self.repo), "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(installed.status(self.repo)["pin"], preview["after"])
        self.assertEqual(len(connection.settings(self.repo)["hooks"]["SessionStart"]), 1)

    def test_subprocess_entry_only_and_same_identity_for_review(self):
        self.configure()
        expected = installed.status(self.repo)["identity"]
        nested = self.repo / "lib/data"
        nested.mkdir(parents=True)
        for event in ("SessionStart", "UserPromptSubmit"):
            result = self.cli("installed-hook", "--runtime", "claude", payload={
                "cwd": str(nested), "hook_event_name": event, "expected": expected})
            text = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn(expected, text)
            entry = resources.files("flutter_agent_guidelines").joinpath("payload/AGENTS.md").read_text()
            if event == "SessionStart":
                self.assertTrue(text.endswith(entry))
            else:
                self.assertNotIn(entry.strip(), text)
                self.assertLess(len(text), len(entry))
                self.assertIn("Selected profiles: none", text)
        self.assertEqual(installed.status(self.repo, expected)["identity"], expected)
        self.assertEqual(sorted(p.name for p in installed.root(self.repo).iterdir()),
                         sorted([installed.pin(self.repo)["bundle"], "connection.json"]))

    def test_tamper_and_symlink_rejection(self):
        self.configure()
        _, directory = installed.verify(self.repo)
        entry = directory / "payload/AGENTS.md"
        entry.chmod(0o644)
        original = entry.read_bytes()
        entry.write_text("tampered")
        with self.assertRaisesRegex(SnapshotError, "content mismatch"):
            installed.context(self.repo)
        entry.write_bytes(original)
        path = self.repo / installed.PIN
        selected = path.read_bytes()
        path.unlink()
        target = self.root / "pin.json"
        target.write_bytes(selected)
        path.symlink_to(target)
        with self.assertRaisesRegex(SnapshotError, "symlink"):
            installed.status(self.repo)

    def test_missing_pin_can_disconnect_but_cannot_silently_repin(self):
        self.configure()
        (self.repo / installed.PIN).unlink()
        with self.assertRaisesRegex(SnapshotError, "restore the versioned pin"):
            installed.configure(self.repo, apply=True)
        result = self.cli("uninstall", "--repo", str(self.repo), "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(connection.record_path(self.repo).exists())

    def test_nested_worktree_cannot_inherit_outer_project_pin(self):
        self.configure()
        nested = self.repo / "nested-worktree"
        nested.mkdir()
        (nested / ".git").write_text("gitdir: elsewhere")
        result = self.cli("installed-hook", "--runtime", "claude", payload={
            "cwd": str(nested), "hook_event_name": "SessionStart"})
        self.assertIn("no installed project pin", json.loads(result.stdout)["systemMessage"])

    def test_uninstall_preserves_unrelated_settings_and_pin(self):
        self.configure()
        value = connection.settings(self.repo)
        value["custom"] = "owner edit after installation"
        guard = {"hooks": [{"type": "command", "command": "ordinary-guard"}]}
        value["hooks"]["PreToolUse"] = [guard]
        save_json(self.repo / connection.SETTINGS, value)
        connection.uninstall(self.repo, apply=True)
        value = connection.settings(self.repo)
        self.assertEqual(value["custom"], "owner edit after installation")
        self.assertEqual(value["hooks"], {"PreToolUse": [guard]})
        self.assertFalse((self.repo / connection.PLUGIN).exists())
        self.assertTrue((self.repo / installed.PIN).exists())
        self.assertEqual(installed.status(self.repo)["installation"], "absent")

    def test_conflicting_loaders_and_legacy_refused(self):
        installed.configure(self.repo, apply=True)
        path = self.repo / ".claude/settings.json"
        path.parent.mkdir()
        save_json(path, {"hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": "other-loader"}]}]}})
        with self.assertRaisesRegex(SnapshotError, "competing loader"):
            connection.install(self.repo, apply=True)
        path.unlink()
        save_json(self.repo / ".flutter-guidelines.json", {})
        with self.assertRaisesRegex(SnapshotError, "legacy configuration"):
            installed.configure(self.repo, apply=True)

    def test_unused_client_loader_is_ignored_but_selected_legacy_tool_hook_is_not(self):
        self.configure("claude")
        plugin = self.repo / connection.PLUGIN
        plugin.parent.mkdir(parents=True)
        plugin.write_text('export const loader = {"experimental.chat.system.transform": true};')
        self.assertEqual(installed.status(self.repo)["installation"], "verified")
        plugin.unlink()
        value = connection.settings(self.repo)
        value["hooks"]["PreToolUse"] = [{"hooks": [{"type": "command", "command":
            "python -I -m flutter_agent_guidelines.cli hook --runtime claude"}]}]
        save_json(self.repo / connection.SETTINGS, value)
        with self.assertRaisesRegex(SnapshotError, "competing loader"):
            installed.status(self.repo)

    def test_single_client_install_verify_and_upgrade_scope_loader_inventory(self):
        config = self.repo / "opencode.json"
        save_json(config, {"instructions": ["unused-opencode-guide.md"]})
        with patch.dict(os.environ, {"OPENCODE_PURE": "1"}):
            self.configure("claude")
            self.assertEqual(installed.status(self.repo)["installation"], "verified")
            installed.upgrade(self.repo, apply=True)
        connection.uninstall(self.repo, apply=True)
        with self.assertRaisesRegex(SnapshotError, "competing loader"):
            connection.install(self.repo, "both")
        config.unlink()
        path = self.repo / ".claude/settings.json"
        save_json(path, {"hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": "unused-claude-loader"}]}]}})
        with patch.dict(os.environ, {"CLAUDE_CODE_SIMPLE": "1"}):
            connection.install(self.repo, "opencode", apply=True)
            self.assertEqual(installed.status(self.repo)["installation"], "verified")
            installed.upgrade(self.repo, apply=True)

    def test_all_claude_events_detect_injection_but_ordinary_guards_coexist(self):
        self.configure("claude")
        value = connection.settings(self.repo)
        value["hooks"]["PostToolUse"] = [{"hooks": [{"type": "command", "command": "ordinary-guard"}]}]
        save_json(self.repo / connection.SETTINGS, value)
        self.assertEqual(installed.status(self.repo)["installation"], "verified")
        value["hooks"]["PostToolUse"][0]["hooks"][0]["command"] = "loader --additionalContext rules"
        save_json(self.repo / connection.SETTINGS, value)
        with self.assertRaisesRegex(SnapshotError, "PostToolUse"):
            installed.status(self.repo)
        with self.assertRaisesRegex(SnapshotError, "PostToolUse"):
            installed.upgrade(self.repo)

    def test_hook_refuses_unselected_and_unknown_runtimes_without_injection(self):
        self.configure("opencode")
        result = self.cli("installed-hook", "--runtime", "claude", payload={
            "cwd": str(self.repo), "hook_event_name": "SessionStart"})
        self.assertNotIn("hookSpecificOutput", json.loads(result.stdout))
        self.assertIn("not selected", json.loads(result.stdout)["systemMessage"])
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            installed.hook("unknown")
        response = json.loads(output.getvalue())
        self.assertIn("unknown installed hook runtime", response["warning"])
        self.assertNotIn("context", response)
        connection.uninstall(self.repo, apply=True)
        connection.install(self.repo, "claude", apply=True)
        result = self.cli("installed-hook", "--runtime", "opencode", payload={"cwd": str(self.repo)})
        self.assertIn("not selected", json.loads(result.stdout)["warning"])

    def test_owned_adapter_tamper_blocks_upgrade_and_uninstall(self):
        self.configure()
        (self.repo / connection.PLUGIN).write_text("owner-modified adapter")
        for operation in (installed.status, installed.upgrade, connection.uninstall):
            with self.assertRaisesRegex(SnapshotError, "adapter changed"):
                operation(self.repo)

    def test_legacy_lifecycle_has_no_installed_state_loop(self):
        self.configure()
        before = (self.repo / installed.PIN).read_bytes()
        for command in ("end", "rebaseline"):
            result = self.cli(command, "--repo", str(self.repo))
            self.assertEqual(result.returncode, 1)
            self.assertIn("no work lifecycle", result.stderr)
        self.assertEqual((self.repo / installed.PIN).read_bytes(), before)

    @unittest.skipUnless(shutil.which("node"), "Node is not available")
    def test_actual_js_adapter_injection_and_mismatch_warning(self):
        self.configure("opencode")
        harness = Path(__file__).with_name("installed_adapter_harness.mjs")
        result = subprocess.run(["node", str(harness), str(self.repo / connection.PLUGIN),
                                 str(self.repo)], capture_output=True, text=True, cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)
