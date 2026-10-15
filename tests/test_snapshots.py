import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from flutter_agent_guidelines import (
    SnapshotError, export_bundle, inspect_package, read_resource, verify_snapshot,
)
from flutter_agent_guidelines.bundles import PAYLOAD
from flutter_agent_guidelines.snapshots import canonical, digest, write_snapshot


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.addCleanup(self.temporary.cleanup)
        # Read-only guards need restoring for portable fixture cleanup.
        self.addCleanup(self.make_writable)

    def make_writable(self):
        for entry in [self.root, *self.root.rglob("*")]:
            if not entry.is_symlink():
                entry.chmod(0o755 if entry.is_dir() else 0o644)

    def test_resources_export_reuse_and_offline_verification(self):
        snapshot = export_bundle(self.root)
        manifest = verify_snapshot(snapshot, snapshot.name)
        self.assertEqual(manifest["metadata"]["version"], "0.1.0.dev0")
        self.assertTrue(manifest["metadata"]["development"])
        self.assertEqual(export_bundle(self.root), snapshot)
        self.assertEqual({name.removeprefix("payload/") for name in manifest["files"]
                          if name.startswith("payload/")}, set(PAYLOAD))
        for name in PAYLOAD:
            self.assertEqual(read_resource(name), (snapshot / "payload" / name).read_bytes())
        for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "provenance/README.md"):
            self.assertIn(name, manifest["files"])
        self.assertEqual(inspect_package()["source_approval"], "not supplied")

    def test_tampered_content_fails_verification_and_cache_reuse(self):
        snapshot = export_bundle(self.root)
        content = snapshot / "payload/AGENTS.md"
        content.chmod(0o644)
        content.write_bytes(b"tampered")
        with self.assertRaises(SnapshotError):
            verify_snapshot(snapshot)
        with self.assertRaises(SnapshotError):
            export_bundle(self.root)

    def test_manifest_and_expected_pin_tampering(self):
        snapshot = export_bundle(self.root)
        with self.assertRaises(SnapshotError):
            verify_snapshot(snapshot, "0" * 64)
        manifest = snapshot / "manifest.json"
        manifest.chmod(0o644)
        manifest.write_bytes(manifest.read_bytes() + b" ")
        with self.assertRaises(SnapshotError):
            verify_snapshot(snapshot)

    def test_extra_file_and_symlink_rejected(self):
        snapshot = export_bundle(self.root)
        snapshot.chmod(0o755)
        extra = snapshot / "extra"
        extra.write_text("not in manifest")
        with self.assertRaises(SnapshotError):
            verify_snapshot(snapshot)
        extra.unlink()
        extra.symlink_to(snapshot / "NOTICE")
        with self.assertRaises(SnapshotError):
            verify_snapshot(snapshot)

    def test_unsafe_paths_and_unknown_resources_rejected(self):
        for name in ("../escape", "/absolute", "a/../b", "a//b", "a\\b", "C:bad", "manifest.json"):
            with self.subTest(name=name), self.assertRaises(SnapshotError):
                write_snapshot(self.root, {name: b"bad"}, {})
        with self.assertRaises(SnapshotError):
            read_resource("../NOTICE")
        link = self.root / "link"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(SnapshotError):
            export_bundle(link)

    def test_existing_user_directory_never_overwritten(self):
        files, metadata = {"a.md": b"hello"}, {}
        identity = digest(canonical({"schema": 1, "metadata": metadata,
                                     "files": {"a.md": digest(b"hello")}}))
        target = self.root / identity
        target.mkdir()
        (target / "user.md").write_text("keep")
        with self.assertRaises((SnapshotError, OSError)):
            write_snapshot(self.root, files, metadata)
        self.assertEqual((target / "user.md").read_text(), "keep")

    def test_hostile_manifest_paths_fail_without_reading_outside(self):
        raw = canonical({"schema": 1, "metadata": {}, "files": {"../escape": "0" * 64}})
        target = self.root / digest(raw)
        target.mkdir()
        (target / "manifest.json").write_bytes(raw)
        with self.assertRaises(SnapshotError):
            verify_snapshot(target)

    def test_malformed_manifest_schema_and_encoding_rejected(self):
        for raw in (canonical({"schema": True, "metadata": {}, "files": {}}), b"\xff"):
            target = self.root / digest(raw)
            target.mkdir()
            (target / "manifest.json").write_bytes(raw)
            with self.subTest(raw=raw), self.assertRaises(SnapshotError):
                verify_snapshot(target)

    def test_cli_outside_checkout_and_exit_status(self):
        executable = "flutter-guidelines.exe" if os.name == "nt" else "flutter-guidelines"
        command = [str(Path(sys.executable).with_name(executable))]
        help_result = subprocess.run(command + ["--help"], cwd=self.root, capture_output=True)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        result = subprocess.run(command + ["inspect"], cwd=self.root, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), inspect_package())
        result = subprocess.run(command + ["export", str(self.root)], cwd=self.root, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        exported = json.loads(result.stdout)
        result = subprocess.run(command + ["verify", exported["snapshot"], "--digest", exported["digest"]],
                                cwd=self.root, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(command + ["verify", exported["snapshot"], "--digest", "0" * 64],
                                cwd=self.root, capture_output=True)
        self.assertEqual(result.returncode, 1)
