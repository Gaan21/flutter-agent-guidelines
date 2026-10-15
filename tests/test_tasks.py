import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from flutter_agent_guidelines import SnapshotError, export_bundle, inspect_package, verify_snapshot
from flutter_agent_guidelines.snapshots import canonical, digest, regular_bytes, write_snapshot
from flutter_agent_guidelines.tasks import join_task, prepare_task


class TaskTests(unittest.TestCase):
    """Synthetic approved release: never a real source or artifact attestation."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(self.make_writable)
        self.consumer = self.root / "consumer"
        self.consumer.mkdir()
        (self.consumer / "AGENTS.md").write_text("Synthetic local policy\n")
        (self.consumer / "overlay.md").write_text("Synthetic overlay\n")
        development = export_bundle(self.root)
        manifest = verify_snapshot(development)
        self.released = inspect_package()
        self.released.update(version="1.0.0", development=False)
        released_metadata = {key: value for key, value in self.released.items() if key != "files"}
        self.bundle = write_snapshot(self.root, {
            name: regular_bytes(development / name) for name in manifest["files"]
        }, released_metadata)
        self.record = {
            "schema": 1, "approved": True, "authority": "synthetic test operator",
            "approval_reference": "fixture-only", "source_url": "https://example.invalid/source",
            "source_sha": "1" * 40, "version": "1.0.0", "artifact_sha256": "2" * 64,
            "bundle_digest": self.bundle.name, "payload_digest": self.released["payload_digest"],
        }
        self.arguments = dict(
            consumer_root=self.consumer, task_id="fixture-task", bundle=self.bundle,
            release_record=canonical(self.record), approved_record_sha256=digest(canonical(self.record)),
            policy_paths=["AGENTS.md"], overlay_paths=["overlay.md"],
            context={"external_contract_pins": {}, "toolchain_configuration": {"fixture": True},
                     "preloads": ["AGENTS.md", "overlay.md"]},
        )

    def make_writable(self):
        for entry in [self.root, *self.root.rglob("*")]:
            if not entry.is_symlink():
                entry.chmod(0o755 if entry.is_dir() else 0o644)

    def prepare(self, **changes):
        with patch("flutter_agent_guidelines.tasks.inspect_package", return_value=copy.deepcopy(self.released)):
            return prepare_task(**(self.arguments | changes))

    def test_roles_share_exact_pin_overlay_and_source_after_local_changes(self):
        task = self.prepare()
        (self.consumer / "overlay.md").write_text("new policy for a future task")
        implementer = join_task(task, consumer_root=self.consumer,
                                expected_digest=task.name, role="implementer")
        # Joining does not inspect installed package or perform a network operation.
        with patch("flutter_agent_guidelines.tasks.inspect_package", side_effect=AssertionError("upgrade")):
            reviewer = join_task(task, consumer_root=self.consumer,
                                 expected_digest=task.name, role="reviewer")
        self.assertEqual(implementer.pop("role"), "implementer")
        self.assertEqual(reviewer.pop("role"), "reviewer")
        self.assertEqual(implementer, reviewer)
        self.assertEqual(reviewer["source_sha"], self.record["source_sha"])
        self.assertEqual((task / "overlay/overlay.md").read_text(), "Synthetic overlay\n")
        with self.assertRaises(SnapshotError):
            self.prepare(task_id="another-task")

    def test_development_install_and_unapproved_sources_rejected(self):
        with self.assertRaises(SnapshotError):
            prepare_task(**self.arguments)
        for changes in ({"approved": False}, {"version": "1.0.0.dev0"},
                        {"source_sha": "short"}, {"payload_digest": "0" * 64},
                        {"bundle_digest": "0" * 64}):
            record = canonical(self.record | changes)
            with self.subTest(changes=changes), self.assertRaises(SnapshotError):
                self.prepare(release_record=record, approved_record_sha256=digest(record))
        with self.assertRaises(SnapshotError):
            self.prepare(approved_record_sha256="0" * 64)

    def test_malformed_release_records_raise_snapshot_error(self):
        for changes in ({"source_url": 123}, {"source_url": "https://[invalid"},
                        {"schema": True}):
            record = canonical(self.record | changes)
            with self.subTest(changes=changes), self.assertRaises(SnapshotError):
                self.prepare(release_record=record, approved_record_sha256=digest(record))
        with self.assertRaises(SnapshotError):
            self.prepare(release_record=b"\xff", approved_record_sha256=digest(b"\xff"))

    def test_invalid_id_policy_path_symlink_and_wrong_consumer(self):
        for task_id in ("../escape", "/absolute", "a/b", "", "a" * 65):
            with self.subTest(task_id=task_id), self.assertRaises(SnapshotError):
                self.prepare(task_id=task_id)
        with self.assertRaises(SnapshotError):
            self.prepare(policy_paths=["../outside"])
        with self.assertRaises(SnapshotError):
            self.prepare(policy_paths=[])
        (self.consumer / "link.md").symlink_to(self.consumer / "AGENTS.md")
        with self.assertRaises(SnapshotError):
            self.prepare(overlay_paths=["link.md"])
        task = self.prepare()
        with self.assertRaises(SnapshotError):
            join_task(task, consumer_root=self.root, expected_digest=task.name, role="reviewer")
        with self.assertRaises(SnapshotError):
            join_task(task, consumer_root=self.consumer, expected_digest="0" * 64, role="reviewer")

    def test_overlay_corruption_rejects_role_join(self):
        task = self.prepare()
        overlay = task / "overlay/overlay.md"
        overlay.chmod(0o644)
        overlay.write_text("tampered")
        with self.assertRaises(SnapshotError):
            join_task(task, consumer_root=self.consumer, expected_digest=task.name, role="reviewer")
