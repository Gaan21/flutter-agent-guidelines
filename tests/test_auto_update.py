"""Real isolated controller processes and trusted local Git; not native client evidence."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_runtime
import flutter_agent_guidelines
from flutter_agent_guidelines import bootstrap, deployments, runtime, SnapshotError
from flutter_agent_guidelines.runtime_io import read_json, save_json


class AutoUpdateTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture = test_runtime.RuntimeTests(methodName="runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.repo, self.source, self.cache = fixture.repo, fixture.source, fixture.cache
        package = Path(flutter_agent_guidelines.__file__).parent
        destination = self.source / "src/flutter_agent_guidelines"
        for path in [*package.glob("*.py"), *package.glob("*.json"), *package.glob("adapters/*.js")]:
            target = destination / path.relative_to(package)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        (self.source / "pyproject.toml").write_text(
            '[project]\nname="flutter-agent-guidelines"\nversion="0.1.0.dev0"\n'
            'requires-python=">=3.11"\ndependencies=[]\n')
        fixture.commit()
        self.revision = fixture.git("rev-parse", "HEAD").strip()
        self.config = fixture.config | {"updates": {"protocol": 1}}
        save_json(self.repo / ".flutter-guidelines.json", self.config)
        fixture.install()

    def start(self, session="one", repo=None, event="SessionStart", **kwargs):
        return bootstrap.handle("claude", {"cwd": str(repo or self.repo), "session_id": session,
                                            "hook_event_name": event, **kwargs})

    def work(self, repo=None):
        return runtime.load_work(repo or self.repo)

    def cli(self, command, *args, repo=None):
        repo = repo or self.repo
        return bootstrap.command(repo, [command, "--repo", str(repo), *args])

    def close(self, sessions=("one",), repo=None):
        self.cli("end", repo=repo)
        for session in sessions:
            self.cli("release", "--runtime", "claude", "--session", session, repo=repo)
        self.assertIsNone(self.work(repo))

    def advance(self):
        entry = self.source / "src/flutter_agent_guidelines/payload/AGENTS.md"
        entry.write_text(entry.read_text() + "\nNew guidance\n")
        controller = self.source / "src/flutter_agent_guidelines/runtime.py"
        controller.write_text(controller.read_text() + "\n# Controller revision two\n")
        adapter = self.source / "src/flutter_agent_guidelines/adapters/opencode.js"
        adapter.write_text(adapter.read_text() + "\n// Adapter revision two\n")
        self.fixture.commit()
        return self.fixture.git("rev-parse", "HEAD").strip()

    def test_new_work_updates_controller_content_and_adapter_without_consumer_edits(self):
        settings = (self.repo / ".claude/settings.local.json").read_bytes()
        plugin = (self.repo / ".opencode/plugins/flutter-guidelines.js").read_bytes()
        config = (self.repo / ".flutter-guidelines.json").read_bytes()
        self.assertIn("hookSpecificOutput", self.start())
        first = self.work()
        first_deployment = read_json(self.repo / ".flutter-guidelines/engine.json")["deployment"]
        self.close()
        revision = self.advance()
        self.assertIn("hookSpecificOutput", self.start("next"))
        second = self.work()
        self.assertEqual(second["revision"], revision)
        self.assertNotEqual(first["controller"], second["controller"])
        second_deployment = read_json(self.repo / ".flutter-guidelines/engine.json")["deployment"]
        self.assertNotEqual(first_deployment, second_deployment)
        self.assertTrue(Path(first_deployment).exists())
        self.assertIn("Adapter revision two", (Path(second_deployment) /
                      "package/flutter_agent_guidelines/adapters/opencode.js").read_text())
        self.assertIn("New guidance", (self.repo / ".flutter-guidelines/snapshots" /
                      second["snapshot"] / "payload/AGENTS.md").read_text())
        self.assertEqual(settings, (self.repo / ".claude/settings.local.json").read_bytes())
        self.assertEqual(plugin, (self.repo / ".opencode/plugins/flutter-guidelines.js").read_bytes())
        self.assertEqual(config, (self.repo / ".flutter-guidelines.json").read_bytes())

    def test_continuation_and_reviewer_remain_on_original_controller(self):
        self.start()
        first = self.work()
        self.advance()
        self.assertIn("hookSpecificOutput", self.start(event="UserPromptSubmit"))
        reviewer = self.cli("join", "--runtime", "opencode", "--session", "review",
                            "--expected", first["snapshot"])
        self.assertEqual(reviewer["work"]["controller"], first["controller"])
        self.assertEqual(reviewer["work"]["revision"], self.revision)
        self.assertEqual(self.work()["snapshot"], first["snapshot"])
        self.assertEqual(self.work()["update"]["state"], "UPDATE")
        self.assertEqual(self.work()["phase"], "active")

    def test_resolution_is_fixed_before_preparing_even_if_channel_moves(self):
        self.advance()
        with patch("flutter_agent_guidelines.bootstrap.resolve", return_value=self.revision) as lookup:
            self.assertIn("hookSpecificOutput", self.start())
        lookup.assert_called_once()
        self.assertEqual(self.work()["revision"], self.revision)
        self.assertEqual(self.work()["update"]["state"], "UPDATE")

    def test_shared_cache_concurrent_consumers_keep_different_deployments(self):
        self.start()
        first = self.work()
        revision = self.advance()
        other = self.fixture.root / "other-consumer"
        other.mkdir()
        for name in ("AGENTS.md", "overlay.md", ".flutter-guidelines.json"):
            shutil.copyfile(self.repo / name, other / name)
        with patch("flutter_agent_guidelines.installation.probe", return_value="2.1.301"):
            from flutter_agent_guidelines.installation import install
            install(other, apply=True)
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda index: self.start(str(index), repo=other), range(3)))
        self.assertTrue(all("hookSpecificOutput" in result for result in results), results)
        self.assertEqual(self.work(other)["revision"], revision)
        self.assertEqual(len(self.work(other)["sessions"]), 3)
        self.assertIn("hookSpecificOutput", self.start())
        self.assertEqual(self.work()["controller"], first["controller"])
        self.assertNotEqual(self.work(other)["controller"], first["controller"])

    def test_network_failure_warns_without_new_identity_and_cached_continuation_works(self):
        self.start()
        first = self.work()
        moved = self.source.with_name("offline")
        self.source.rename(moved)
        self.assertIn("hookSpecificOutput", self.start(event="UserPromptSubmit"))
        self.assertEqual(self.work()["snapshot"], first["snapshot"])
        self.assertEqual(self.work()["update"]["state"], "UNKNOWN")
        self.close()
        failed = self.start("next")
        self.assertIn("freshness UNKNOWN", failed["systemMessage"])
        self.assertIsNone(self.work())
        moved.rename(self.source)
        self.assertIn("hookSpecificOutput", self.start("next"))

    def test_interrupted_preparation_is_not_activated_and_retry_recovers(self):
        with patch("flutter_agent_guidelines.deployments.invoke", side_effect=SnapshotError("interrupted")):
            failed = self.start()
        self.assertIn("interrupted", failed["systemMessage"])
        self.assertIsNone(self.work())
        self.assertFalse((self.repo / ".flutter-guidelines/engine.json").exists())
        # An orphan left by SIGKILL has no index; future preparations ignore it.
        abandoned = self.cache / "controllers/staging-interrupted"
        abandoned.mkdir()
        (abandoned / "partial.py").write_text("partial")
        self.assertIn("hookSpecificOutput", self.start())
        self.assertTrue(abandoned.exists())

    def test_fixed_revision_offline_and_future_rollback_leave_active_work_unchanged(self):
        self.start()
        first = self.work()
        new_revision = self.advance()
        bootstrap.track(self.repo, self.revision, apply=True)
        self.assertEqual(self.work()["snapshot"], first["snapshot"])
        self.close()
        self.source.rename(self.source.with_name("offline"))
        self.assertIn("hookSpecificOutput", self.start("fixed"))
        self.assertEqual(self.work()["revision"], self.revision)
        self.assertNotEqual(self.work()["revision"], new_revision)

    def test_unapproved_source_and_tampered_deployment_are_never_executed(self):
        save_json(self.repo / ".flutter-guidelines.json", self.config | {"updates": None})
        with patch("flutter_agent_guidelines.deployments.invoke", side_effect=AssertionError("executed")):
            self.assertIn("systemMessage", self.start())
        save_json(self.repo / ".flutter-guidelines.json", self.config)
        self.start()
        pointer = read_json(self.repo / ".flutter-guidelines/engine.json")
        path = Path(pointer["deployment"]) / "package/flutter_agent_guidelines/engine.py"
        path.chmod(0o644)
        path.write_text("raise RuntimeError('tampered')")
        with patch("flutter_agent_guidelines.deployments.invoke", side_effect=AssertionError("executed")):
            self.assertIn("systemMessage", self.start())

    def test_incompatible_adapter_protocol_requires_explicit_migration(self):
        contract = self.source / "src/flutter_agent_guidelines/bootstrap-contract.json"
        contract.write_text('{"protocol":2}')
        self.fixture.commit()
        failed = self.start()
        self.assertRegex(failed["systemMessage"], "incompatible|migrate")
        self.assertIsNone(self.work())
        self.assertFalse((self.repo / ".flutter-guidelines/engine.json").exists())

    def test_changed_guard_review_still_prevents_execution(self):
        settings = self.repo / ".claude/settings.local.json"
        original = settings.read_bytes()
        value = json.loads(original)
        value["hooks"]["PreToolUse"].append({"hooks": [{"type": "command", "command": "unreviewed"}]})
        save_json(settings, value)
        with patch("flutter_agent_guidelines.deployments.invoke", side_effect=AssertionError("executed")):
            self.assertIn("systemMessage", self.start())
        self.assertIsNone(self.work())

    def test_reconfigure_migration_is_explicit_and_blocked_until_uninstall(self):
        from flutter_agent_guidelines.installation import configure, uninstall
        without_updates = {key: value for key, value in self.config.items() if key != "updates"}
        with self.assertRaisesRegex(SnapshotError, "uninstall"):
            configure(self.repo, self.config["source"], ["AGENTS.md"], ["overlay.md"],
                      self.cache, apply=True)
        uninstall(self.repo, apply=True)
        save_json(self.repo / ".flutter-guidelines.json", without_updates)
        configure(self.repo, self.config["source"], ["AGENTS.md"], ["overlay.md"],
                  self.cache, auto_update=True)
        self.assertNotIn("updates", read_json(self.repo / ".flutter-guidelines.json"))
        configure(self.repo, self.config["source"], ["AGENTS.md"], ["overlay.md"],
                  self.cache, apply=True, auto_update=True)
        self.fixture.install()
        self.assertIn("hookSpecificOutput", self.start())

    def test_source_controller_symlink_or_new_dependency_cannot_be_activated(self):
        engine = self.source / "src/flutter_agent_guidelines/engine.py"
        original = engine.read_bytes()
        engine.unlink()
        engine.symlink_to(self.source / "NOTICE")
        self.fixture.commit()
        self.assertIn("nonregular", self.start()["systemMessage"])
        self.assertIsNone(self.work())
        engine.unlink()
        engine.write_bytes(original)
        project = self.source / "pyproject.toml"
        project.write_text(project.read_text().replace("dependencies=[]", 'dependencies=["unexpected"]'))
        self.fixture.commit()
        self.assertIn("incompatible", self.start()["systemMessage"])
        self.assertIsNone(self.work())

    def test_leases_closure_and_rebaseline_do_not_upgrade_or_bypass_protection(self):
        self.start()
        first = self.work()
        self.advance()
        (self.repo / "AGENTS.md").write_text("Changed local authority")
        self.assertIn("rebaseline", self.start(event="UserPromptSubmit")["systemMessage"])
        self.assertEqual(self.work()["phase"], "rebaseline-required")
        with self.assertRaises(SnapshotError):
            self.cli("rebaseline", "--apply")
        with self.assertRaises(SnapshotError):
            self.cli("end")
        self.cli("release", "--runtime", "claude", "--session", "one")
        replacement = self.cli("rebaseline", "--apply")["work"]
        self.assertEqual(replacement["controller"], first["controller"])
        self.assertEqual(replacement["revision"], first["revision"])
        self.assertNotEqual(replacement["snapshot"], first["snapshot"])
        self.assertIn("hookSpecificOutput", self.start("renewed"))
        self.cli("end")
        self.assertIn("closing", self.start("cannot-join")["systemMessage"])
        self.assertTrue(self.work()["sessions"])
        with self.assertRaisesRegex(SnapshotError, "protected"):
            self.start(event="PreToolUse", tool_name="Write", tool_input={"file_path": str(self.cache)})

    def test_native_session_cannot_silently_start_another_work(self):
        self.start()
        self.close()
        self.assertIn("new native conversation", self.start()["systemMessage"])
        self.assertIsNone(self.work())

    def test_stable_claude_protocol_preserves_parent_lease_across_subprocess(self):
        def hook(event):
            return subprocess.run([sys.executable, "-I", "-m", "flutter_agent_guidelines.cli",
                                   "bridge", "--runtime", "claude"], text=True, capture_output=True,
                                  input=json.dumps({"cwd": str(self.repo), "session_id": "native",
                                                    "hook_event_name": event}))
        result = hook("SessionStart")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("hookSpecificOutput", json.loads(result.stdout))
        self.assertEqual(len(self.work()["sessions"]), 1)
        result = hook("SessionEnd")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.work()["sessions"])

    def test_versioned_opencode_hooks_via_stable_dispatcher(self):
        if not shutil.which("node"):
            self.skipTest("Node unavailable")
        harness = Path(__file__).with_name("auto_adapter_harness.mjs")
        result = subprocess.run(["node", str(harness), str(self.repo), str(self.source), sys.executable], text=True,
                                capture_output=True, timeout=100)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)
