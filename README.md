# flutter-agent-guidelines

**0.1.0.dev0 — local development distribution.** Original Flutter engineering guidance with a small Python resource/snapshot tool. Python >=3.11; no application dependencies. Distribution: `flutter-agent-guidelines`; import: `flutter_agent_guidelines`; CLI: `flutter-guidelines`.

## Build and install locally

From this repository root, using a supported Python interpreter:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade build setuptools wheel
.venv/bin/python -m build
.venv/bin/python -m pip install --no-deps dist/flutter_agent_guidelines-0.1.0.dev0-py3-none-any.whl
.venv/bin/flutter-guidelines --help
```

Use your available Python >=3.11 executable in the first command. On Windows, virtual-environment executables live under `Scripts` rather than `bin`. These are local build/install instructions; no PyPI or pub.dev release is claimed. Avoid editable installs for content identity. Installation does not configure a consumer.

## Inspect, export, verify

```sh
.venv/bin/flutter-guidelines inspect
mkdir guidance-exports
.venv/bin/flutter-guidelines export guidance-exports
```

- `inspect`: JSON package version, development marker, payload digest and exact file hashes; source approval explicitly absent.
- `export PARENT`: existing parent required. Creates `PARENT/<manifest-sha256>/` containing the five Markdown resources, license/notices/provenance and canonical `manifest.json`. Prints absolute snapshot path and digest. Existing identical snapshots are verified and reused; corruption fails.
- `verify SNAPSHOT --digest EXPECTED_SHA256`: offline integrity check, including exact inventory and all file hashes. Use the printed snapshot path and separately retained digest. `--digest` is optional for self-consistency checking; that alone does not authenticate content.
- CLI exits 0 on success, 1 on integrity/I/O errors, 2 on argument errors. JSON results on stdout; errors on stderr.

Paths must not contain symlinks or traversal, including ancestor links. On systems where a temporary-directory alias is a symlink, supply its canonical physical path. Existing user files are never unconditionally overwritten. No archive extraction or shell/product command execution occurs.

Exported bytes are immutable by contract. Read-only modes discourage accidental edits; they do not isolate hostile same-user processes. Interrupted creation can leave an incomplete directory: verification fails closed, and the operator must inspect/recover it before reuse. There is no cache pruning operation.

## Python resources and task API

```python
from flutter_agent_guidelines import export_bundle, read_resource, verify_snapshot

entry = read_resource("AGENTS.md")  # bytes, allowlisted resource name
snapshot = export_bundle("guidance-exports")  # existing directory
manifest = verify_snapshot(snapshot, expected_digest=snapshot.name)
```

Install the wheel first. Payload reads use `importlib.resources`; notices use installed distribution metadata. The package never writes into installed resources.

[`docs/task-api.md`](docs/task-api.md) documents the limited `prepare_task` / `join_task` API: one exclusive consumer task slot, approved common source record, snapshotted local policy/overlay, exact digest joins and externally retained role receipts. **This development installation cannot prepare operational tasks.** Synthetic tests inject a stable release fixture; no actual release/source approval is manufactured.

## Content and authority

- Consumer entry: [`payload/AGENTS.md`](src/flutter_agent_guidelines/payload/AGENTS.md). Root [`AGENTS.md`](AGENTS.md) is maintainer policy, not shipped consumer authority.
- Canonical payload: entry, engineering boundaries, reliability, verification procedure and on-demand upstream index. Local consumer architecture/security/contracts remain authoritative.
- Offline durable-local acceptance remains visibly pending until remote acknowledgment. Upstream recommendation strength is preserved; architecture/generators/offline protocols are not universal mandates.
- Written guidance is not installed enforcement. Inspect standard lint version/include chain/severity/exclusions and executed outcomes; standard context/sink/Future checks have bounded predicates. No custom lint source, rule pack, analyzer config or validation harness is supplied.
- No skills auto-discovery, runtime launch, hooks/plugins, update fetcher, finish/session management or automatic consumer activation. Future adapters must explicitly load the pinned consumer entry, expose namespaced procedures/skills from the same bundle, and verify the same manifest for both roles in tested Claude Code/OpenCode versions. Markdown links alone do not establish loading.

## Verification and release

```sh
.venv/bin/python tests/check_distribution.py
```

The proof script copies an allowlisted source tree to a temporary directory outside the checkout, builds sdist and wheel (wheel from sdist), checks exact payload/notices, installs in a new environment and runs stdlib tests from outside the source checkout. It leaves artifacts/environments in its printed directory for inspection. Tests cover offline reuse, corruption, path/link rejection, no-overwrite and synthetic two-role task identity. No Flutter SDK or consumer behavioral checks are implied. Actual runtime/platform evidence belongs in the delivery report; minimum-version and multi-OS coverage require separate runs.

Before an approved stable release:

1. Review exact public inventory, provenance and version; run package proof on supported targets.
2. Build from approved public source; retain source full SHA, artifact SHA-256 and exported bundle/payload digests in an **external** release attestation. Authenticate source and verify artifact outside this package; never embed a self-referential source SHA.
3. Operator approves the exact release record through its own trusted channel. Installing a wheel or passing an arbitrary SHA does not supply that trust.
4. Obtain separate authorization for publishing and consumer activation. Git remains human-controlled.

## License and provenance

Apache-2.0 for owner-authorized original material; see [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and [`provenance/README.md`](provenance/README.md). Prior original guidance adapted with owner authorization; no private source dependency. Third parties are linked, not relicensed or vendored. Flutter/Dart names do not imply official endorsement.
