"""Review regressions: context budgets, logical scope and bounded guard approval."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from flutter_agent_guidelines import SnapshotError, read_resource
from flutter_agent_guidelines import installation, runtime
from flutter_agent_guidelines.git_source import validate_source
from flutter_agent_guidelines.hook_reviews import hook_inventory
from flutter_agent_guidelines.runtime_io import read_json, save_json
import test_runtime


class RuntimeReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_runtime.RuntimeTests(methodName="runTest")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.repo = self.fixture.repo

    def cli(self, *args):
        return subprocess.run([sys.executable, "-I", "-m", "flutter_agent_guidelines.cli", *args],
                              capture_output=True, text=True, cwd=self.fixture.root)

    def guard_settings(self, name=".claude/settings.local.json"):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        value = {"permissions": {"deny": ["Bash(rm *)"]}, "hooks": {"PreToolUse": [
            {"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "existing-quality-guard",
                                               "timeout": 20, "onFailure": "block"}]}]}}
        save_json(path, value)
        return path, value

    def approve(self):
        item, = hook_inventory(self.repo)
        installation.review_guard(self.repo, item["source"], item["digest"], True, True)
        return item

    def test_claude_context_budget_start_resume_compact_prompt_and_tools(self):
        self.fixture.install()
        entry = read_resource("AGENTS.md").decode()
        for source in ("startup", "resume", "compact"):
            result = self.fixture.hook("SessionStart", source=source)
            self.assertEqual(result.returncode, 0, result.stderr)
            full = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertEqual(full.count(entry), 1)
        result = self.fixture.hook("UserPromptSubmit")
        self.assertEqual(result.returncode, 0, result.stderr)
        short = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertLess(len(short), len(full) // 2)
        self.assertNotIn(entry.splitlines()[0], short)
        for required in ("Flutter work", "source", "digest", "Verified Guidelines-Root:", "Updates:"):
            self.assertIn(required, short)
        allowed = self.fixture.hook("PreToolUse", tool_name="Read", tool_input={"file_path": "AGENTS.md"})
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(json.loads(allowed.stdout), {})

    def test_scoped_index_keeps_unrelated_policies_out_of_global_context(self):
        paths = ["lib_a/AGENTS.md", "lib_b/AGENTS.md", ".claude/rules/private.md",
                 "lib_a/deep/CLAUDE.md"]
        for name in paths:
            target = self.repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('---\npaths:\n  - "lib_b/**/*.dart"\n---\nPath-specific rule\n'
                              if name.startswith(".claude") else "Nested policy\n")
        self.fixture.config["policies"].extend(paths)
        save_json(self.repo / ".flutter-guidelines.json", self.fixture.config)
        result = self.fixture.join()
        context = result["context"]
        self.assertIn("local/policies/AGENTS.md", context)
        self.assertIn("local/overlays/overlay.md", context)
        self.assertIn("policy-index.json", context)
        self.assertIn("cwd/touched-file ancestor", context)
        for name in paths:
            self.assertNotIn(name, context)
            self.assertIn("local/policies/" + name, result["work"]["local"])
        snapshot = Path(result["root"])
        index = read_json(snapshot / "policy-index.json")
        entries = {item["logical_path"]: item for item in index["entries"]}
        self.assertEqual(entries[paths[0]]["scope"], {"kind": "ancestor-chain", "directory": "lib_a"})
        self.assertEqual(entries[paths[1]]["scope"], {"kind": "ancestor-chain", "directory": "lib_b"})
        self.assertEqual(entries[paths[2]]["scope"]["kind"], "native-rule")
        self.assertEqual(entries[paths[2]]["scope"]["selector_base"], ".")
        self.assertEqual((snapshot / entries[paths[2]]["snapshot_path"]).read_bytes(),
                         (self.repo / paths[2]).read_bytes())
        (self.repo / paths[2]).write_text("changed conditional rule")
        with self.assertRaises(SnapshotError):
            self.fixture.join()

    def test_reviewed_guard_plan_cli_inventory_preservation_and_uninstall(self):
        path, original = self.guard_settings()
        before = path.read_bytes()
        with self.assertRaises(SnapshotError) as error:
            self.fixture.install()
        item, = hook_inventory(self.repo)
        self.assertIn(item["digest"], str(error.exception))
        inventory = self.cli("inventory-hooks", "--repo", str(self.repo))
        self.assertEqual(inventory.returncode, 0, inventory.stderr)
        self.assertEqual(json.loads(inventory.stdout)["hooks"], [item])
        command = ["review-guard", "--repo", str(self.repo), "--source", item["source"],
                   "--digest", item["digest"], "--non-instruction-guard"]
        planned = self.cli(*command)
        self.assertEqual(planned.returncode, 0, planned.stderr)
        self.assertNotIn("reviewed_guards", read_json(self.repo / ".flutter-guidelines.json"))
        approved = self.cli(*command, "--apply")
        self.assertEqual(approved.returncode, 0, approved.stderr)
        self.fixture.install()
        installed = read_json(path)
        self.assertEqual(installed["permissions"], original["permissions"])
        self.assertEqual(installed["hooks"]["PreToolUse"][:-1], original["hooks"]["PreToolUse"])
        self.assertEqual(self.fixture.hook("SessionStart").returncode, 0)
        self.assertEqual(self.fixture.hook("SessionEnd").returncode, 0)
        runtime.lifecycle(self.repo, "end")
        installation.uninstall(self.repo, True)
        self.assertEqual(path.read_bytes(), before)

    def test_changed_missing_or_moved_reviewed_guard_invalidates_runtime_approval(self):
        path, original = self.guard_settings(".claude/settings.json")
        item = self.approve()
        self.fixture.install()
        for change in ("handler", "selector", "missing", "source"):
            value = json.loads(json.dumps(original))
            if change == "handler":
                value["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = "changed-guard"
            elif change == "selector":
                value["hooks"]["PreToolUse"][0]["matcher"] = "Bash"
            elif change == "missing":
                value["hooks"]["PreToolUse"] = []
            else:
                value["hooks"]["PreToolUse"] = []
                save_json(self.repo / ".claude/moved.json", original)
            save_json(path, value)
            result = self.fixture.hook("UserPromptSubmit")
            self.assertEqual(result.returncode, 0, change)
            self.assertIn("systemMessage", json.loads(result.stdout))
            self.assertNotIn("additionalContext", result.stdout)
            self.assertIn(item["digest"], result.stderr)
            self.assertIn("missing/changed", result.stderr)
            with self.assertRaises(SnapshotError):
                self.fixture.join()
        save_json(path, original)
        self.assertEqual(self.fixture.hook("UserPromptSubmit").returncode, 0)

    def test_unknown_guard_and_startup_prompt_loaders_cannot_share_an_approval(self):
        path, value = self.guard_settings()
        item = self.approve()
        for event in ("PreToolUse", "SessionStart", "UserPromptSubmit"):
            changed = json.loads(json.dumps(value))
            group = ({"hooks": [{"type": "command", "command": "unknown-guard"}]}
                     if event == "PreToolUse" else value["hooks"]["PreToolUse"][0])
            changed["hooks"].setdefault(event, []).append(group)
            save_json(path, changed)
            with self.assertRaises(SnapshotError):
                self.fixture.install()
        save_json(path, value)
        with self.assertRaises(SnapshotError):
            installation.review_guard(self.repo, item["source"], item["digest"])
        invalid = self.fixture.config | {"reviewed_guards": [{"source": item["source"],
            "event": "SessionStart", "digest": item["digest"], "purpose": "non-instruction-guard"}]}
        save_json(self.repo / ".flutter-guidelines.json", invalid)
        with self.assertRaises(SnapshotError):
            runtime.configuration(self.repo)

    def test_copied_work_state_cannot_join_a_different_consumer(self):
        self.fixture.join()
        other = self.fixture.root / "different-consumer"
        shutil.copytree(self.repo, other)
        with self.assertRaisesRegex(SnapshotError, "different consumer worktree"):
            runtime.join(other, "opencode", "reviewer")

    def test_configuration_malformed_types_and_source_urls_raise_snapshot_error(self):
        changes = [{"schema": True}, {"policies": [None]}, {"policies": [{}]},
                   {"policies": [["AGENTS.md"]]}, {"overlays": [1]}, {"overlays": "overlay.md"},
                   {"cache": []}, {"source": None}, {"reviewed_guards": [None]}]
        for change in changes:
            save_json(self.repo / ".flutter-guidelines.json", self.fixture.config | change)
            with self.subTest(change=change), self.assertRaises(SnapshotError):
                runtime.configuration(self.repo)
        with self.assertRaises(SnapshotError):
            validate_source({"url": "https://[invalid", "ref": "refs/heads/main"})
