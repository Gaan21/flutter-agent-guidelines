"""Regression coverage for degraded conversation and explicit replacement preparation."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_runtime
from flutter_agent_guidelines import SnapshotError, runtime
from flutter_agent_guidelines.adapters import handle, guard
from flutter_agent_guidelines.runtime_io import read_json


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        fixture = test_runtime.RuntimeTests(methodName="runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.repo = fixture.repo
        self.join, self.install, self.hook = fixture.join, fixture.install, fixture.hook

    def test_nested_policy_recovery_keeps_source_and_replaces_identity(self):
        self.install()
        first = self.join()
        nested = self.repo / "lib/AGENTS.md"
        nested.parent.mkdir()
        nested.write_text("Scoped local authority")
        for name, arguments in (("Read", {"file_path": str(nested)}),
                                ("Edit", {"file_path": str(nested)}),
                                ("Write", {"file_path": "lib/feature.dart"})):
            response = self.hook("PreToolUse", tool_name=name, tool_input=arguments)
            self.assertEqual(response.returncode, 0, response.stderr)
            self.assertIn("rebaseline required", json.loads(response.stdout)["systemMessage"])
        work = runtime.lifecycle(self.repo, "status")["work"]
        self.assertEqual(work["phase"], "rebaseline-required")
        self.assertEqual(work["snapshot"], first["work"]["snapshot"])
        with self.assertRaisesRegex(SnapshotError, "rebaseline required"):
            runtime.lifecycle(self.repo, "end")
        with self.assertRaisesRegex(SnapshotError, "exit all sessions"):
            runtime.rebaseline(self.repo, True)
        runtime.lifecycle(self.repo, "release", "claude", "one")
        plan = runtime.rebaseline(self.repo)
        self.assertIn("lib/AGENTS.md", plan["policies"])
        self.assertEqual(read_json(self.repo / ".flutter-guidelines/work.json"),
                         runtime.lifecycle(self.repo, "status")["work"])
        with patch("flutter_agent_guidelines.runtime.resolve", side_effect=AssertionError("latest")):
            replacement = runtime.rebaseline(self.repo, True)["work"]
            joined = self.join("renewed", expected=replacement["snapshot"])
        self.assertEqual(replacement["revision"], first["work"]["revision"])
        self.assertNotEqual(replacement["snapshot"], first["work"]["snapshot"])
        self.assertNotEqual(replacement["id"], first["work"]["id"])
        self.assertEqual(replacement["phase"], "active")
        self.assertTrue((Path(joined["root"]) / "local/policies/lib/AGENTS.md").is_file())
        self.assertEqual(runtime.join(self.repo, "opencode", "reviewer", expected=replacement["snapshot"])
                         ["work"]["snapshot"], replacement["snapshot"])
        with self.assertRaises(SnapshotError):
            self.join("stale", expected=first["work"]["snapshot"])

    def test_reverted_policy_still_requires_rebaseline(self):
        self.join()
        path = self.repo / "AGENTS.md"
        original = path.read_bytes()
        path.write_text("changed")
        with self.assertRaises(runtime.PolicyDrift):
            self.join()
        path.write_bytes(original)
        with self.assertRaisesRegex(SnapshotError, "rebaseline required"):
            runtime.lifecycle(self.repo, "end")

    def test_rebaseline_rejects_external_policy_delegation_and_tamper(self):
        first = self.join()
        runtime.lifecycle(self.repo, "release", "claude", "one")
        policy = self.repo / "AGENTS.md"
        policy.write_text("Read [authority](../external/AGENTS.md)")
        with self.assertRaisesRegex(SnapshotError, "external instruction delegation"):
            runtime.rebaseline(self.repo, True)
        policy.write_text("Local authority")
        entry = Path(first["root"]) / "payload/AGENTS.md"
        entry.chmod(0o644)
        entry.write_text("tampered")
        with self.assertRaises(SnapshotError):
            runtime.rebaseline(self.repo, True)
        self.assertEqual(read_json(self.repo / ".flutter-guidelines/work.json")["snapshot"],
                         first["work"]["snapshot"])

    def test_runtime_failure_warns_but_guard_runs_first(self):
        self.install()
        payload = {"cwd": str(self.repo), "session_id": "native", "hook_event_name": "SessionStart"}
        with patch("flutter_agent_guidelines.adapters.verify_adapter", side_effect=OSError("unavailable")):
            result = handle("claude", payload)
            self.assertIn("unavailable", result["systemMessage"])
            self.assertNotIn("hookSpecificOutput", result)
            payload |= {"hook_event_name": "PreToolUse", "tool_name": "Read",
                        "tool_input": {"file_path": ".flutter-guidelines/work.json"}}
            self.assertIn("systemMessage", handle("claude", payload))
            payload["tool_name"] = "Write"
            with self.assertRaisesRegex(SnapshotError, "protected"):
                handle("claude", payload)

    def test_protected_shell_inspection_uses_read(self):
        self.join()
        for command in ("ls", "cat", "head", "grep"):
            with self.assertRaisesRegex(SnapshotError, "protected"):
                guard(self.repo, "Bash", {"command": f"{command} .flutter-guidelines/work.json"})
        guard(self.repo, "Read", {"file_path": ".flutter-guidelines/work.json"})
