"""Git fixtures are explicitly trusted test sources, never release records."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from flutter_agent_guidelines import SnapshotError
from flutter_agent_guidelines.bundles import package_files
from flutter_agent_guidelines import installation, runtime
from flutter_agent_guidelines.adapters import guard
from flutter_agent_guidelines.git_source import materialize
from flutter_agent_guidelines.runtime_io import consumer_root, discover, read_json, save_json


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="flutter-runtime-fixture-")).resolve()
        environment = patch.dict(os.environ, {"HOME": str(self.root / "home"),
            "CLAUDE_CONFIG_DIR": str(self.root / "home/.claude"),
            "XDG_CONFIG_HOME": str(self.root / "home/config")})
        environment.start()
        self.addCleanup(environment.stop)
        for key in ("OPENCODE_CONFIG", "OPENCODE_CONFIG_CONTENT"):
            os.environ.pop(key, None)
        self.source = self.root / "source"
        self.source.mkdir()
        self.repo = self.root / "consumer"
        self.repo.mkdir()
        self.cache = self.root / "cache"
        for name, content in package_files().items():
            destination = self.source / ("src/flutter_agent_guidelines/" + name
                                         if name.startswith("payload/") else name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        self.git("init", "-b", "main")
        self.commit()
        self.revision = self.git("rev-parse", "HEAD").strip()
        (self.repo / "AGENTS.md").write_text("Local authority\n")
        (self.repo / "overlay.md").write_text("Local overlay\n")
        self.config = {"schema": 1, "source": {"url": str(self.source),
                       "ref": "refs/heads/main", "trusted_fixture": True},
                       "policies": ["AGENTS.md"], "overlays": ["overlay.md"],
                       "cache": str(self.cache)}
        save_json(self.repo / ".flutter-guidelines.json", self.config)

    def git(self, *args):
        result = subprocess.run(["git", "-c", "user.name=Fixture", "-c",
                                 "user.email=fixture@example.invalid", *args],
                                cwd=self.source, capture_output=True, text=True, check=True)
        return result.stdout

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-m", "fixture")

    def join(self, session="one", **kwargs):
        return runtime.join(self.repo, "claude", session, **kwargs)

    def install(self, choice="both"):
        with patch("flutter_agent_guidelines.installation.probe", return_value="2.1.301"):
            return installation.install(self.repo, choice, apply=True)

    def hook(self, event, **extra):
        payload = {"cwd": str(self.repo), "session_id": "native",
                   "hook_event_name": event, **extra}
        return subprocess.run([sys.executable, "-I", "-m", "flutter_agent_guidelines.cli",
                               "hook", "--runtime", "claude"], input=json.dumps(payload),
                              text=True, capture_output=True, cwd=self.root)

    def test_remote_movement_unpublished_edits_and_two_roles(self):
        entry = self.source / "src/flutter_agent_guidelines/payload/AGENTS.md"
        entry.write_text("unpublished working change")
        first = self.join()
        self.assertEqual(first["work"]["revision"], self.revision)
        self.assertNotIn("unpublished", (Path(first["root"]) / "payload/AGENTS.md").read_text())
        self.commit()
        update = runtime.lifecycle(self.repo, "refresh-check")["work"]
        self.assertEqual(update["update"]["state"], "UPDATE")
        self.assertEqual(update["snapshot"], first["work"]["snapshot"])
        reviewer = runtime.join(self.repo, "opencode", "review", "reviewer",
                                first["work"]["snapshot"])
        self.assertEqual(reviewer["root"], first["root"])
        self.assertEqual(len(reviewer["work"]["sessions"]), 2)
        with self.assertRaises(SnapshotError):
            self.join("wrong", expected="0" * 64)

    def test_offline_resume_unknown_and_first_start_block(self):
        first = self.join()
        moved = self.source.with_name("unavailable")
        self.source.rename(moved)
        resumed = self.join(refresh=True)
        self.assertEqual(resumed["root"], first["root"])
        self.assertEqual(resumed["work"]["update"]["state"], "UNKNOWN")

    def test_offline_network_failure(self):
        first = self.join()
        with patch("flutter_agent_guidelines.runtime.resolve", side_effect=SnapshotError("offline")):
            resumed = self.join(refresh=True)
            self.assertEqual(resumed["work"]["update"]["state"], "UNKNOWN")
            self.assertEqual(resumed["root"], first["root"])
        runtime.lifecycle(self.repo, "end")
        runtime.lifecycle(self.repo, "release", "claude", "one")
        with patch("flutter_agent_guidelines.git_source.resolve", side_effect=SnapshotError("offline")):
            with self.assertRaises(SnapshotError):
                self.join("new")
        self.assertFalse((self.repo / ".flutter-guidelines/work.json").exists())

    def test_policy_overlay_config_and_controller_drift(self):
        self.join()
        for name in ("AGENTS.md", "overlay.md"):
            path = self.repo / name
            before = path.read_bytes()
            path.write_bytes(b"changed")
            with self.assertRaises(SnapshotError):
                self.join()
            path.write_bytes(before)
        config = self.repo / ".flutter-guidelines.json"
        save_json(config, self.config | {"cache": str(self.root / "other")})
        with self.assertRaises(SnapshotError):
            self.join()
        save_json(config, self.config)
        with patch("flutter_agent_guidelines.runtime.controller_identity", return_value={}):
            with self.assertRaises(SnapshotError):
                self.join()

    def test_concurrent_first_joins_and_closing(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda index: self.join(str(index)), range(4)))
        self.assertEqual(len({result["root"] for result in results}), 1)
        closing = runtime.lifecycle(self.repo, "end")
        self.assertFalse(closing["closed"])
        with self.assertRaises(SnapshotError):
            self.join("new")
        self.join("0")
        for index in range(4):
            released = runtime.lifecycle(self.repo, "release", "claude", str(index))
        self.assertTrue(released["closed"])
        self.assertNotEqual(self.join("next")["root"], results[0]["root"])

    def test_tamper_symlink_config_paths_and_corrupt_state(self):
        first = self.join()
        entry = Path(first["root"]) / "payload/AGENTS.md"
        entry.chmod(0o644)
        entry.write_text("tampered")
        with self.assertRaises(SnapshotError):
            self.join()
        state = self.repo / ".flutter-guidelines/work.json"
        state.write_text("{}")
        with self.assertRaises(SnapshotError):
            self.join()
        self.assertEqual(state.read_text(), "{}")
        with self.assertRaises(SnapshotError):
            materialize(self.config["source"], self.root / "../escape")

    def test_source_symlink_and_exact_commit(self):
        source = self.config["source"] | {"ref": self.revision}
        entry = self.source / "src/flutter_agent_guidelines/payload/AGENTS.md"
        entry.unlink()
        entry.symlink_to(self.source / "NOTICE")
        self.commit()
        with self.assertRaises(SnapshotError):
            materialize(self.config["source"], self.cache)
        revision, _, _ = materialize(source, self.cache)
        self.assertEqual(revision, self.revision)

    def test_safe_install_plan_idempotence_uninstall_and_backup_recovery(self):
        settings = self.repo / ".claude/settings.local.json"
        settings.parent.mkdir()
        original = (b'{"permissions":{"deny":["Bash(rm *)"]},"hooks":{"PostToolUse":'
                    b'[{"hooks":[{"type":"command","command":"existing-check"}]}]}}\n')
        settings.write_bytes(original)
        with patch("flutter_agent_guidelines.installation.probe", return_value="2.1.301"):
            installation.install(self.repo)
        self.assertFalse((self.repo / ".flutter-guidelines").exists())
        self.assertEqual(settings.read_bytes(), original)
        self.install()
        before = settings.read_bytes()
        self.install()
        self.assertEqual(settings.read_bytes(), before)
        value = json.loads(before)
        self.assertEqual(value["permissions"], {"deny": ["Bash(rm *)"]})
        self.assertEqual(value["hooks"]["PostToolUse"], json.loads(original)["hooks"]["PostToolUse"])
        self.assertEqual(value["hooks"]["SessionStart"][0]["hooks"][0]["onFailure"], "block")
        settings.write_bytes(before + b" ")
        with self.assertRaises(SnapshotError):
            installation.uninstall(self.repo, True)
        backup = read_json(self.repo / ".flutter-guidelines/installation.json")
        self.assertIsNotNone(backup["files"][".claude/settings.local.json"]["before"])
        settings.write_bytes(before)
        record = self.repo / ".flutter-guidelines/installation.json"
        corrupted = dict(backup)
        corrupted["files"] = {"/unexpected/external": next(iter(backup["files"].values()))}
        save_json(record, corrupted)
        with self.assertRaises(SnapshotError):
            installation.uninstall(self.repo, True)
        save_json(record, backup)
        installation.uninstall(self.repo, True)
        self.assertEqual(settings.read_bytes(), original)
        self.assertFalse((self.repo / ".opencode/plugins/flutter-guidelines.js").exists())

    def test_conflicting_loader_and_jsonc_preservation(self):
        config = self.repo / "opencode.jsonc"
        content = '// comment\n{"permission":{"edit":"deny"}}'
        config.write_text(content)
        self.install("opencode")
        self.assertEqual(config.read_text(), content)
        installation.uninstall(self.repo, True)
        config.write_text('{"instructions":["other-authority.md"]}')
        with self.assertRaises(SnapshotError):
            self.install()

    def test_claude_stdin_schema_blocks_and_parent_release(self):
        self.install()
        nested = self.repo / "lib/nested"
        nested.mkdir(parents=True)
        self.git("-C", str(self.repo), "init")
        self.assertEqual(discover(nested), self.repo)
        with self.assertRaises(SnapshotError):
            consumer_root(nested)
        start = self.hook("SessionStart", cwd=str(nested))
        self.assertEqual(start.returncode, 0, start.stderr)
        output = json.loads(start.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SessionStart")
        self.assertIn("Verified Guidelines-Root:", output["additionalContext"])
        prompt = self.hook("UserPromptSubmit")
        self.assertEqual(prompt.returncode, 0, prompt.stderr)
        denied = self.hook("PreToolUse", tool_name="Write",
                           tool_input={"file_path": ".flutter-guidelines/work.json"})
        self.assertEqual(denied.returncode, 2)
        self.assertIn("protected", denied.stderr)
        allowed = self.hook("PreToolUse", tool_name="Read",
                            tool_input={"file_path": ".flutter-guidelines/work.json"})
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(json.loads(allowed.stdout), {})
        self.hook("SessionEnd", agent_id="child")
        self.assertTrue(read_json(self.repo / ".flutter-guidelines/work.json")["sessions"])
        self.assertEqual(self.hook("SessionEnd").returncode, 0)
        self.assertFalse(read_json(self.repo / ".flutter-guidelines/work.json")["sessions"])
        (self.repo / "AGENTS.md").write_text("drift")
        failed = self.hook("UserPromptSubmit")
        self.assertEqual(failed.returncode, 2)
        self.assertIn("drift", failed.stderr)

    def test_alias_targets_and_live_adapter_mismatch(self):
        first = self.join(adapter="first")
        with self.assertRaises(SnapshotError):
            self.join(adapter="changed")
        alias = self.repo / "alias"
        alias.symlink_to(first["root"], target_is_directory=True)
        with self.assertRaises(SnapshotError):
            guard(self.repo, "edit", {"filePath": "alias/payload/AGENTS.md"})

    def test_missing_git_offline_resume_and_stale_resolution(self):
        entry = self.source / "src/flutter_agent_guidelines/payload/AGENTS.md"
        entry.write_text("future revision")
        self.commit()
        with patch("flutter_agent_guidelines.git_source.resolve", return_value=self.revision):
            first = self.join()
        self.assertEqual(first["work"]["revision"], self.revision)
        with patch.dict(os.environ, {"PATH": ""}):
            resumed = self.join(refresh=True)
            self.assertEqual(resumed["work"]["update"]["state"], "UNKNOWN")
            self.assertEqual(resumed["root"], first["root"])

    def test_two_instances_of_same_native_session_hold_independent_leases(self):
        self.join(lease="instance-a")
        self.join(lease="instance-b")
        runtime.lifecycle(self.repo, "end")
        first = runtime.lifecycle(self.repo, "release", "claude", "one", "instance-a")
        self.assertFalse(first["closed"])
        with self.assertRaises(SnapshotError):
            self.join("new")
        final = runtime.lifecycle(self.repo, "release", "claude", "one", "instance-b")
        self.assertTrue(final["closed"])

    def test_global_loader_and_external_instruction_delegation_refused(self):
        directory = Path(os.environ["CLAUDE_CONFIG_DIR"])
        directory.mkdir(parents=True)
        save_json(directory / "settings.json", {"hooks": {"SessionStart": [
            {"hooks": [{"type": "command", "command": "unknown-instruction-loader"}]}]}})
        with self.assertRaises(SnapshotError):
            self.install()
        (directory / "settings.json").unlink()
        (self.repo / "AGENTS.md").write_text("Read [authority](../external/AGENTS.md)")
        with self.assertRaises(SnapshotError):
            self.install()

    def test_new_native_policy_and_disabled_hooks_fail_closed(self):
        self.join()
        rules = self.repo / ".claude/rules"
        rules.mkdir(parents=True)
        (rules / "private.md").write_text("new auto-loaded rule")
        with self.assertRaises(SnapshotError):
            self.join()
        (rules / "private.md").unlink()
        save_json(self.repo / ".claude/settings.local.json", {"disableAllHooks": True})
        with self.assertRaises(SnapshotError):
            self.install()

    def test_node_adapter_real_controller(self):
        if not shutil.which("node"):
            self.skipTest("Node unavailable")
        self.install("opencode")
        harness = Path(__file__).with_name("adapter_harness.mjs")
        result = subprocess.run(["node", str(harness), str(self.repo)],
                                capture_output=True, text=True, cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)
