"""Disposable maintainer experiments, not consumer integration tests."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--tool-dir', required=True, type=Path,
                    help='Disposable npm prefix containing rulesync 36.0.2')
parser.add_argument('--source-ref', required=True,
                    help='Approved public source revision, resolved once for the checks')
parser.add_argument('--workspace', required=True, type=Path,
                    help='New disposable directory outside the checkout')
args, test_args = parser.parse_known_args()
BASE = args.workspace.absolute()
if BASE.exists() or BASE.is_symlink() or ROOT == BASE or ROOT in BASE.resolve().parents:
    parser.error('workspace must be new and outside the checkout')
CLI = args.tool_dir.resolve() / 'node_modules/.bin/rulesync'
package = json.loads((args.tool_dir / 'node_modules/rulesync/package.json').read_text())
if package['version'] != '36.0.2':
    parser.error('these checks target rulesync 36.0.2')
SOURCE = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', '--verify',
                                 '--end-of-options', args.source_ref + '^{commit}'],
                                text=True).strip()
BASE.mkdir()
ENV = {'PATH': os.environ['PATH'], 'HOME': str(BASE / 'home'),
       'XDG_CONFIG_HOME': str(BASE / 'home/config'),
       'XDG_CACHE_HOME': str(BASE / 'home/cache'),
       'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
       'GIT_TERMINAL_PROMPT': '0'}
NETWORK_DENIED = ['sandbox-exec', '-p', '(version 1)(allow default)(deny network*)']
spec = importlib.util.spec_from_file_location('exporter', ROOT / 'tools/export_rulesync_trial.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + '\n')


def inventory(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob('*')) if p.is_file()}


class Verification(unittest.TestCase):
    def setUp(self):
        self.workspace = BASE / self.id().split('.')[-1]
        self.workspace.mkdir()

    def run_cli(self, *args, code=0, offline=False):
        command = (NETWORK_DENIED if offline else []) + [str(CLI), *args]
        result = subprocess.run(command, cwd=self.workspace, env=ENV,
                                text=True, capture_output=True, timeout=90)
        with (BASE / 'commands.log').open('a') as log:
            log.write(f'{self.workspace.name}: {args} offline={offline} exit={result.returncode}\n')
            log.write(result.stdout + result.stderr + '\n')
        if code is not None:
            self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def export(self):
        # Exporter requires a new destination.
        self.workspace.rmdir()
        return exporter.export(self.workspace, SOURCE, architecture=True)

    def nonroot(self):
        write(self.workspace / 'rulesync.jsonc', {
            'targets': ['claudecode', 'opencode'], 'features': ['rules'], 'delete': False})
        write(self.workspace / '.rulesync/rules/flutter.md',
              '---\nroot: false\ntargets: [claudecode, opencode]\n'
              'description: Fixture entry\n---\n\nRead topics only when relevant.\n')

    def test_01_deterministic_offline_and_tamper(self):
        self.export()
        independent = BASE / 'independent-export'
        exporter.export(independent, SOURCE, architecture=True)
        self.assertEqual(inventory(self.workspace), inventory(independent))
        probe = subprocess.run(NETWORK_DENIED + ['curl', '--max-time', '5',
                               'https://registry.npmjs.org/rulesync'],
                               env=ENV, capture_output=True, text=True)
        self.assertNotEqual(probe.returncode, 0)
        self.assertTrue(any(word in probe.stderr.lower() for word in
                            ('not permitted', 'resolve', 'connect')), probe.stderr)
        self.run_cli('generate')
        first = inventory(self.workspace)
        self.run_cli('generate', offline=True)
        self.assertEqual(first, inventory(self.workspace))
        self.run_cli('generate', '--check', offline=True)
        entry = self.workspace / 'AGENTS.md'
        original = entry.read_bytes()
        entry.write_text('tampered\n')
        self.run_cli('generate', '--check', code=1, offline=True)
        entry.unlink()
        self.run_cli('generate', '--check', code=1, offline=True)
        entry.write_bytes(original)
        topic = self.workspace / '.guidelines-trial/payload/profiles/architecture.md'
        topic.write_text('tampered topic\n')
        self.run_cli('generate', '--check', offline=True)
        manifest = json.loads((self.workspace / 'trial-manifest.json').read_text())
        key = str(topic.relative_to(self.workspace))
        self.assertNotEqual(manifest['files'][key], inventory(self.workspace)[key])
        topic.unlink()
        self.run_cli('generate', '--check', offline=True)
        self.assertNotIn(key, inventory(self.workspace))
        rule = self.workspace / '.rulesync/rules/flutter.md'
        rule.write_text(rule.read_text() + '\nChanged source.\n')
        self.run_cli('generate', '--check', code=1, offline=True)

    def test_02_nonroot_jsonc_merge(self):
        self.nonroot()
        config = self.workspace / 'opencode.jsonc'
        write(config, '// consumer comment\n' + json.dumps({
            '$schema': 'https://opencode.ai/config.json',
            'instructions': ['docs/local.md', '.opencode/memories/consumer-owned.md'],
            'permission': {'edit': 'ask'}, 'plugin': ['./guard.js'],
            'mcp': {'fixture': {'type': 'local', 'command': ['fixture-not-executed']}}}))
        write(self.workspace / 'AGENTS.md', '# Local authority\n')
        write(self.workspace / 'CLAUDE.md', '# Claude local authority\n')
        self.run_cli('generate', offline=True)
        # JSONC is parsed using the exact dependency rulesync installed.
        parsed = subprocess.check_output(['node', '-e',
            "const fs=require('fs');const j=require(process.argv[1]);"
            "console.log(JSON.stringify(j.parse(fs.readFileSync(process.argv[2],'utf8'))));",
            str(args.tool_dir.resolve() / 'node_modules/jsonc-parser'), str(config)], text=True)
        value = json.loads(parsed)
        self.assertEqual(value['permission'], {'edit': 'ask'})
        self.assertEqual(value['plugin'], ['./guard.js'])
        self.assertEqual(value['mcp']['fixture']['command'], ['fixture-not-executed'])
        self.assertEqual(value['instructions'], ['.opencode/memories/flutter.md', 'docs/local.md'])
        self.assertIn('// consumer comment', config.read_text())
        self.assertEqual((self.workspace / 'AGENTS.md').read_text(), '# Local authority\n')
        self.assertEqual((self.workspace / 'CLAUDE.md').read_text(), '# Claude local authority\n')
        first = inventory(self.workspace)
        self.run_cli('generate', offline=True)
        self.assertEqual(first, inventory(self.workspace))

    def test_03_nonroot_json_merge(self):
        self.nonroot()
        config = self.workspace / 'opencode.json'
        write(config, {'$schema': 'https://opencode.ai/config.json',
                       'instructions': ['docs/local.md'], 'permission': {'edit': 'deny'}})
        self.run_cli('generate', offline=True)
        value = json.loads(config.read_text())
        self.assertEqual(value['permission'], {'edit': 'deny'})
        self.assertIn('docs/local.md', value['instructions'])
        self.assertFalse((self.workspace / 'opencode.jsonc').exists())

    def test_04_nested_config_not_merged(self):
        self.nonroot()
        config = self.workspace / '.opencode/opencode.jsonc'
        write(config, {'$schema': 'https://opencode.ai/config.json',
                       'instructions': ['docs/local.md'], 'permission': {'edit': 'deny'}})
        before = config.read_bytes()
        self.run_cli('generate', offline=True)
        self.assertEqual(config.read_bytes(), before)
        self.assertTrue((self.workspace / 'opencode.jsonc').exists())

    def test_05_skill_support_files(self):
        write(self.workspace / 'rulesync.jsonc', {
            'targets': ['claudecode', 'opencode'], 'features': ['skills'], 'delete': False})
        skill = self.workspace / '.rulesync/skills/flutter-fixture'
        write(skill / 'SKILL.md', '---\nname: flutter-fixture\n'
              'description: Consult Flutter fixture guidance.\n---\n\nRead references/topic.md.\n')
        write(skill / 'references/topic.md', '# Fixture topic\n')
        write(skill / 'data.json', {'fixture': True})
        self.run_cli('generate', offline=True)
        for target in ('.claude', '.opencode'):
            output = self.workspace / target / 'skills/flutter-fixture'
            self.assertEqual((output / 'data.json').read_bytes(), (skill / 'data.json').read_bytes())
            self.assertEqual((output / 'references/topic.md').read_bytes(),
                             (skill / 'references/topic.md').read_bytes())
        self.assertFalse((self.workspace / 'opencode.jsonc').exists())
        output_topic = self.workspace / '.opencode/skills/flutter-fixture/references/topic.md'
        output_topic.write_text('tampered\n')
        self.run_cli('generate', '--check', code=1, offline=True)
        output_topic.unlink()
        self.run_cli('generate', '--check', code=1, offline=True)

    def test_06_exact_git_source_and_frozen_cache(self):
        write(self.workspace / 'rulesync.jsonc', {
            'targets': ['claudecode', 'opencode'], 'features': ['rules'],
            'sources': [{'source': ROOT.as_uri(), 'transport': 'git', 'ref': SOURCE,
                         'rulesPath': 'src/flutter_agent_guidelines/payload',
                         'rules': ['AGENTS']}]})
        self.run_cli('install', '--frozen', code=1, offline=True)
        # Git transport resolves via ls-remote, which does not accept a raw SHA.
        failed = self.run_cli('install', code=1, offline=True)
        self.assertIn('not found', failed.stdout + failed.stderr)
        config = json.loads((self.workspace / 'rulesync.jsonc').read_text())
        branch = subprocess.check_output(['git', '-C', str(ROOT), 'symbolic-ref',
                                          '--short', 'HEAD'], text=True).strip()
        config['sources'][0]['ref'] = branch
        expected_ref = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse',
                                               'refs/heads/' + branch], text=True).strip()
        write(self.workspace / 'rulesync.jsonc', config)
        self.run_cli('install', offline=True)
        lock = self.workspace / 'rulesync.lock'
        original_lock = lock.read_bytes()
        value = json.loads(original_lock)
        self.assertEqual(next(iter(value['sources'].values()))['resolvedRef'], expected_ref)
        curated = self.workspace / '.rulesync/rules/.curated/AGENTS.md'
        expected = subprocess.check_output(['git', '-C', str(ROOT), 'show',
                    expected_ref + ':src/flutter_agent_guidelines/payload/AGENTS.md'])
        self.assertEqual(curated.read_bytes(), expected)
        self.run_cli('install', '--frozen', offline=True)
        self.assertEqual(lock.read_bytes(), original_lock)

    def test_07_github_sha_and_offline_cache(self):
        write(self.workspace / 'rulesync.jsonc', {
            'targets': ['claudecode', 'opencode'], 'features': ['rules'],
            'sources': [{'source': 'Gaan21/flutter-agent-guidelines@' + SOURCE,
                         'rulesPath': 'src/flutter_agent_guidelines/payload',
                         'rules': ['AGENTS']}]})
        self.run_cli('install')
        lock = self.workspace / 'rulesync.lock'
        original_lock = lock.read_bytes()
        value = json.loads(original_lock)
        self.assertEqual(next(iter(value['sources'].values()))['resolvedRef'], SOURCE)
        curated = self.workspace / '.rulesync/rules/.curated/AGENTS.md'
        expected = subprocess.check_output(['git', '-C', str(ROOT), 'show',
                    SOURCE + ':src/flutter_agent_guidelines/payload/AGENTS.md'])
        self.assertEqual(curated.read_bytes(), expected)
        self.run_cli('install', '--frozen', offline=True)
        self.assertEqual(lock.read_bytes(), original_lock)
        curated.write_text('tampered cache\n')
        self.run_cli('install', '--frozen', code=1, offline=True)
        self.assertEqual(lock.read_bytes(), original_lock)
        curated.write_bytes(expected)
        config_path = self.workspace / 'rulesync.jsonc'
        config = json.loads(config_path.read_text())
        config['sources'][0]['rules'].append('unlocked-selection')
        write(config_path, config)
        self.run_cli('install', '--frozen', code=1, offline=True)
        self.assertEqual(lock.read_bytes(), original_lock)


if __name__ == '__main__':
    (BASE / 'home').mkdir(exist_ok=True)
    unittest.main(argv=[__file__, *test_args], verbosity=2)
