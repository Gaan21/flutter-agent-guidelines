"""Recorded lint pairing is portable integrity evidence, not runtime attestation."""

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from flutter_agent_guidelines import installed, installed_contract as contracts
from flutter_agent_guidelines import bundles
from flutter_agent_guidelines import installed_installation as connection
from flutter_agent_guidelines.runtime_io import save_json
from flutter_agent_guidelines.snapshots import SnapshotError, digest


def fixture():
    rules = {name: {"enabled": enabled, "options": {}, "severity": "INFO"}
             for name, enabled in contracts.selection().items()}
    rules["require_explicit_types"]["options"] = {"policy": "selective"}
    return {"schema": 1, "package": "dart_architecture_lints", "version": "0.0.6",
            "profile": "architecture", "source_digest": "a" * 64, "rules": rules}


class LintContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="lint-pair-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "project"
        self.repo.mkdir()
        self.path = self.root / "lint-export.json"
        self.value = fixture()
        self.path.write_bytes(contracts.canonical_contract(self.value))
        environment = patch.dict(os.environ, {"HOME": str(self.root / "home"),
            "CLAUDE_CONFIG_DIR": str(self.root / "home/.claude"),
            "XDG_CONFIG_HOME": str(self.root / "home/config")})
        environment.start()
        self.addCleanup(environment.stop)
        for key in ("OPENCODE_CONFIG", "OPENCODE_CONFIG_CONTENT", "OPENCODE_PURE",
                    "OPENCODE_DISABLE_PROJECT_CONFIG", "CLAUDE_CODE_SIMPLE", "CLAUDE_CODE_SAFE_MODE"):
            os.environ.pop(key, None)

    def cli(self, *args):
        return subprocess.run([sys.executable, "-I", "-m", "flutter_agent_guidelines.cli", *args],
                              capture_output=True, text=True, cwd=self.root)

    def connect(self):
        installed.configure(self.repo, apply=True, profiles=["architecture"], lint_contract=self.path)
        connection.install(self.repo, "claude", apply=True)

    def test_cli_pair_preview_portable_identity_and_truthful_context(self):
        args = ("configure", "--installed", "--repo", str(self.repo),
                "--profile", "architecture", "--lint-contract", str(self.path))
        original = self.path.read_bytes()
        preview = self.cli(*args)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(list(self.repo.iterdir()), [])
        self.assertEqual(self.path.read_bytes(), original)
        proposed = json.loads(preview.stdout)
        self.assertEqual(proposed["pin"]["lint_contract"], self.value)
        self.assertEqual(proposed["pin"]["lint_contract_digest"], digest(original))
        self.assertNotIn(str(self.path), json.dumps(proposed["pin"]))
        result = self.cli(*args, "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["identity"], proposed["identity"])
        connection.install(self.repo, "claude", apply=True)
        status = installed.status(self.repo)
        self.assertEqual(status["lint_contract"]["state"], "recorded, not installed-runtime verified")
        self.assertEqual(status["lint_contract"]["source_digest"], self.value["source_digest"])
        text = installed.context(self.repo, include_entry=False)
        self.assertIn("RECORDED, NOT installed-runtime verified", text)
        self.assertIn(digest(original), text)
        self.assertIn("dart_architecture_lints 0.0.6", text)
        other = self.root / "reviewer"
        other.mkdir()
        shutil.copyfile(self.repo / installed.PIN, other / installed.PIN)
        self.path.unlink()
        with patch("subprocess.run", side_effect=AssertionError("pairing must be offline")):
            connection.install(other, "claude", apply=True)
            self.assertEqual(installed.status(other, status["identity"])["pin"], status["pin"])

    def test_reordered_unicode_json_has_same_contract_and_project_identity(self):
        self.value["rules"]["logger_context_matches_scope"]["options"] = {
            "logger_names": ["é", "😀"], "𐀀": "supplementary", "\ue000": "BMP"}
        canonical = contracts.canonical_contract(self.value)
        self.assertLess(canonical.index('"𐀀"'.encode()), canonical.index('"\ue000"'.encode()))
        self.path.write_bytes(canonical)
        first = installed.configure(self.repo, profiles=["architecture"], lint_contract=self.path)
        reordered = {key: self.value[key] for key in reversed(list(self.value))}
        self.path.write_text(json.dumps(reordered, ensure_ascii=False, indent=4) + "\n")
        second = installed.configure(self.repo, profiles=["architecture"], lint_contract=self.path)
        self.assertEqual(first["identity"], second["identity"])
        self.assertEqual(first["pin"]["lint_contract_digest"], digest(canonical))
        changed = copy.deepcopy(self.value)
        changed["rules"]["logger_context_matches_scope"]["options"]["logger_names"].reverse()
        self.assertNotEqual(contracts.canonical_contract(changed), canonical)

    def test_contract_change_requires_upgrade_omission_preserves_and_clear_is_explicit(self):
        self.connect()
        before = installed.status(self.repo)
        directory = installed.root(self.repo) / before["pin"]["bundle"]
        export_before = {p.relative_to(directory): p.read_bytes() for p in directory.rglob("*") if p.is_file()}
        changed = copy.deepcopy(self.value)
        changed["rules"]["method_order"]["severity"] = "ERROR"
        self.path.write_bytes(contracts.canonical_contract(changed))
        self.assertEqual(installed.configure(self.repo)["pin"], before["pin"])
        self.assertEqual(installed.upgrade(self.repo)["after"], before["pin"])
        with self.assertRaisesRegex(SnapshotError, "upgrade-installed"):
            installed.configure(self.repo, apply=True, lint_contract=self.path)
        before_tree = set(self.repo.rglob("*"))
        preview = installed.upgrade(self.repo, lint_contract=self.path)
        self.assertNotEqual(preview["identity"], before["identity"])
        self.assertEqual(set(self.repo.rglob("*")), before_tree)
        self.assertEqual(installed.pin(self.repo), before["pin"])
        applied = self.cli("upgrade-installed", "--repo", str(self.repo), "--lint-contract", str(self.path), "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual(installed.pin(self.repo)["lint_contract"], changed)
        with self.assertRaisesRegex(SnapshotError, "independently retained"):
            installed.status(self.repo, before["identity"])
        self.assertEqual(export_before, {p.relative_to(directory): p.read_bytes()
                                        for p in directory.rglob("*") if p.is_file()})
        with self.assertRaisesRegex(SnapshotError, "upgrade-installed"):
            installed.configure(self.repo, clear_lint_contract=True)
        cleared = self.cli("upgrade-installed", "--repo", str(self.repo), "--clear-lint-contract", "--apply")
        self.assertEqual(cleared.returncode, 0, cleared.stderr)
        self.assertNotIn("lint_contract", installed.pin(self.repo))
        self.assertNotIn("lint_contract_digest", installed.pin(self.repo))
        self.assertEqual(installed.status(self.repo)["lint_contract"]["state"], "unrecorded")

    def test_guidance_only_is_allowed_but_pair_requires_selected_profile(self):
        installed.configure(self.repo, apply=True, profiles=["architecture"])
        connection.install(self.repo, "claude", apply=True)
        self.assertIn("Lint contract: unrecorded", installed.context(self.repo))
        with self.assertRaisesRegex(SnapshotError, "architecture selection required"):
            installed.identity([], self.value)
        installed.upgrade(self.repo, apply=True, lint_contract=self.path)
        with self.assertRaisesRegex(SnapshotError, "architecture selection required"):
            installed.upgrade(self.repo, profiles=[])
        installed.upgrade(self.repo, apply=True, profiles=[], clear_lint_contract=True)
        self.assertEqual(installed.pin(self.repo)["profiles"], [])

    def test_schema_rule_ids_selection_and_selective_policy_are_strict(self):
        bad = []
        for key, value in (("extra", 1), ("schema", True), ("package", "other"),
                           ("version", "latest"), ("profile", "other"), ("source_digest", "A" * 64)):
            sample = copy.deepcopy(self.value)
            sample[key] = value
            bad.append(sample)
        for edit in ("missing", "extra", "enabled", "severity", "options", "field", "policy", "selection"):
            sample = copy.deepcopy(self.value)
            rule = sample["rules"]["require_explicit_types"]
            if edit == "missing":
                sample["rules"].pop("method_order")
            elif edit == "extra":
                sample["rules"]["unknown_diagnostic"] = copy.deepcopy(rule)
            elif edit == "enabled":
                rule["enabled"] = 1
            elif edit == "severity":
                rule["severity"] = "warning"
            elif edit == "options":
                rule["options"] = []
            elif edit == "field":
                rule["extra"] = True
            elif edit == "policy":
                rule["options"]["policy"] = "blanket"
            else:
                sample["rules"]["variable_name_should_contain_class_name"]["enabled"] = False
            bad.append(sample)
        for sample in bad:
            with self.subTest(sample=sample):
                self.path.write_text(json.dumps(sample))
                with patch("flutter_agent_guidelines.installed.export_bundle",
                           side_effect=AssertionError("invalid contracts cannot be exported")):
                    with self.assertRaises(SnapshotError):
                        installed.configure(self.repo, profiles=["architecture"], lint_contract=self.path)
                self.assertEqual(list(self.repo.iterdir()), [])

    def test_bounded_json_rejects_duplicates_nonfinite_depth_size_and_symlinks(self):
        for raw in (b'{"schema":1,"schema":1}', b'{"options":NaN}', b'{"options":1e999}',
                    b"[" * 30 + b"0" + b"]" * 30, b" " * (contracts.MAX_BYTES + 1)):
            self.path.write_bytes(raw)
            with self.assertRaises(SnapshotError):
                contracts.load(self.path)
        self.path.write_bytes(b'{"options":"\\ud800"}')
        with self.assertRaisesRegex(SnapshotError, "Unicode"):
            contracts.load(self.path)
        self.path.unlink()
        self.path.symlink_to(self.repo / "nonexistent")
        with self.assertRaisesRegex(SnapshotError, "symlink"):
            contracts.load(self.path)

    def test_embedded_digest_and_independent_expected_identity_detect_tamper(self):
        self.connect()
        expected = installed.status(self.repo)["identity"]
        value = installed.pin(self.repo)
        value["lint_contract"]["source_digest"] = "b" * 64
        save_json(self.repo / installed.PIN, value)
        with self.assertRaisesRegex(SnapshotError, "contract digest mismatch"):
            installed.status(self.repo)
        value["lint_contract_digest"] = digest(contracts.canonical_contract(value["lint_contract"]))
        save_json(self.repo / installed.PIN, value)
        with self.assertRaisesRegex(SnapshotError, "independently retained"):
            installed.status(self.repo, expected)
        value.pop("lint_contract_digest")
        save_json(self.repo / installed.PIN, value)
        with self.assertRaisesRegex(SnapshotError, "recorded together"):
            installed.pin(self.repo)

    def test_obsolete_selection_can_be_explicitly_replaced_or_cleared(self):
        self.connect()
        value = installed.pin(self.repo)
        value["lint_contract"]["rules"]["method_order"]["enabled"] = False
        value["lint_contract_digest"] = digest(contracts.canonical_contract(value["lint_contract"]))
        save_json(self.repo / installed.PIN, value)
        with self.assertRaisesRegex(SnapshotError, "enabled states"):
            installed.status(self.repo)
        installed.upgrade(self.repo, apply=True, clear_lint_contract=True)
        self.assertEqual(installed.status(self.repo)["lint_contract"]["state"], "unrecorded")

    def test_changed_packaged_profile_fingerprint_refuses_export_and_selection_drift(self):
        self.connect()
        before = installed.pin(self.repo)
        original = bundles.read_resource

        def changed(name):
            content = original(name)
            return content + b"\nProfile revision changed.\n" if name == "profiles/architecture.md" else content

        with patch("flutter_agent_guidelines.bundles.read_resource", side_effect=changed):
            with patch("flutter_agent_guidelines.installed.export_bundle",
                       side_effect=AssertionError("package mismatch must not export")):
                with self.assertRaisesRegex(SnapshotError, "installed package differs"):
                    connection.install(self.repo, "claude", apply=True)
        self.assertEqual(installed.pin(self.repo), before)
        text = original("profiles/architecture.md").replace(
            b"| `no_bang_operator` | disabled |", b"| `no_bang_operator` | enabled |")
        with patch("flutter_agent_guidelines.installed_contract.read_resource", return_value=text):
            with self.assertRaisesRegex(SnapshotError, "enabled states"):
                installed.status(self.repo)

    def test_cli_contract_options_require_installed_mode_and_are_exclusive(self):
        for args, message in (
                (("--lint-contract", str(self.path)), "requires configure --installed"),
                (("--installed", "--lint-contract", str(self.path), "--clear-lint-contract"), "not allowed")):
            result = self.cli("configure", "--repo", str(self.repo), *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(message, result.stderr)
            self.assertEqual(list(self.repo.iterdir()), [])
