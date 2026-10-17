"""Contract checks for the disposable rulesync trial exporter."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
trial = None
if (ROOT / ".git").exists() and (ROOT / "tools/export_rulesync_trial.py").is_file():
    SPEC = importlib.util.spec_from_file_location(
        "rulesync_trial", ROOT / "tools/export_rulesync_trial.py"
    )
    trial = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(trial)


@unittest.skipIf(trial is None, "Trial exporter requires the Git source checkout")
class RulesyncTrialTests(unittest.TestCase):
    def test_export_preserves_source_and_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "trial"
            result = trial.export(output)
            manifest = json.loads((output / "trial-manifest.json").read_text())
            self.assertEqual(result["manifest_sha256"], trial.digest(
                (output / "trial-manifest.json").read_bytes()))
            for path, record in manifest["source_files"].items():
                original = trial.git("show", result["source_revision"] + ":" + path)
                self.assertEqual(original, (output / record["export"]).read_bytes())
            rule = (output / ".rulesync/rules/flutter.md").read_text()
            for path in ("decisions/boundaries.md", "procedures/verification.md",
                         "profiles/architecture.md", "references/upstream.md"):
                self.assertIn("](.guidelines-trial/payload/" + path + ")", rule)
                self.assertTrue((output / ".guidelines-trial/payload" / path).is_file())
            self.assertEqual(manifest["profile"], "generic")

    def test_reproducible_and_explicit_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = trial.export(Path(temporary) / "first")
            second = trial.export(Path(temporary) / "second", first["source_revision"])
            strict = trial.export(Path(temporary) / "strict", first["source_revision"], True)
            self.assertEqual(first, second)
            self.assertNotEqual(first["manifest_sha256"], strict["manifest_sha256"])
            self.assertEqual(strict["profile"], "architecture")

    def test_refuses_existing_or_checkout_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "keep.txt"
            marker.write_text("keep")
            with self.assertRaises(ValueError):
                trial.export(temporary)
            self.assertEqual(marker.read_text(), "keep")
        with self.assertRaises(ValueError):
            trial.export(ROOT / "must-not-create-trial")


if __name__ == "__main__":
    unittest.main()
