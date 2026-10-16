# Limited task snapshot API, schema 1

This Python-only artifact API stores and verifies explicit task inputs. It is not a release authenticator or automatic runtime. The separate approved-Git CLI/adapters use [runtime.md](runtime.md); their automatic work slot does not reuse this artifact API's slot.

Opt-in [automatic Git controller updates](automatic-updates.md) do not make this API
an installed factory integration or waive its stable-release approval requirement.
Factory coordinator lifecycle and instruction-delivery integration remain separate.

## Trust before integrity

An operator must authenticate an approved source/release, verify the installed artifact against its attestation, inspect the exported bundle and approve the exact external record. `approved_record_sha256` is the **out-of-band approved digest of that record**, not evidence obtained by simply hashing an arbitrary supplied record. This package compares identities; it supplies no trust store, signature verifier, Git source verification, artifact-download verification or network resolver.

Artifact preparation rejects development packages even with a record claiming approval. Its stable path is exercised only by explicitly synthetic release fixtures. Approved-Git runtime trials do not require or fabricate an artifact release record.

External UTF-8 JSON release record fields (exact schema; no production example values):

| Field | Required value |
|---|---|
| `schema` | Integer `1` |
| `approved` | Boolean `true`, approved through operator policy |
| `authority`, `approval_reference` | Nonempty operator authority and durable approval reference |
| `source_url` | HTTPS public source URL without credentials; caller authenticates it |
| `source_sha` | Full lowercase 40-character Git SHA, independently verified by operator |
| `version` | Stable `X.Y.Z`; must match installed package; development/pre-releases rejected |
| `artifact_sha256` | Lowercase SHA-256 of the externally verified installed artifact; retained evidence, not checked against an available wheel by this API |
| `bundle_digest` | SHA-256 of canonical exported manifest; must match exported bundle |
| `payload_digest` | SHA-256 of canonical payload file-hash map from `inspect`; must match installed package |

The bundle includes notices and version metadata as well as payload. `bundle_digest` and `payload_digest` have different meanings. Canonical JSON uses sorted keys, compact separators, ASCII escapes and one final newline. File contents are hashed as bytes. Source/artifact/record digests remain distinct.

## Preparation

After a future approved stable release, the caller can use this interface:

```python
from flutter_agent_guidelines.tasks import prepare_task

task = prepare_task(
    consumer_root=consumer_root,  # explicit absolute existing physical path
    task_id=task_id,
    bundle=exported_bundle_path,
    release_record=approved_record_bytes,
    approved_record_sha256=out_of_band_record_digest,
    policy_paths=["AGENTS.md"],
    overlay_paths=["docs/agent-overlay.md"],
    context={
        "external_contract_pins": verified_contract_pins,
        "toolchain_configuration": verified_toolchain_evidence,
        "preloads": verified_preloads,
    },
)
```

- Task ID: 1–64 ASCII letters/digits/underscore/hyphen, beginning with a letter/digit. Paths: explicit safe relative regular-file lists, no traversal or symlinks. At least one local policy required; an empty overlay list is an explicit caller choice.
- Caller lists **all** authoritative policy/overlay and relevant configuration files. The tool cannot infer completeness. External pins/toolchain/preloads are caller-verified JSON evidence, retained in task identity; their semantics or command outcomes are not independently validated.
- Bundle must verify and exactly match installed package content/version/metadata and approved record. The source record, complete common bundle, policy bytes and overlay bytes are copied into the task.
- One exclusive `.flutter-guidelines-task/<task-manifest-digest>/` slot per consumer root/worktree. Any existing slot blocks preparation, even for a different task ID. No live overwrite or automatic rebaseline. Separate tasks require separate worktrees; archive/recovery is an explicit operator action after sessions end.
- Snapshot metadata records consumer/task identity, complete source record, approved record digest, common bundle digest, policy/overlay aggregate digests and context. The outer file-hash map covers every copied file and record.
- Creation reserves a directory exclusively; concurrent creation fails. Readers during incomplete creation fail closed. This is not an active-session lock or a transactional filesystem sandbox. Do not archive or remove an active task.

## Role joins and offline use

```python
from flutter_agent_guidelines.tasks import join_task

receipt = join_task(
    task,
    consumer_root=consumer_root,
    expected_digest=independently_retained_task_digest,
    role="reviewer",  # or "implementer"
)
```

- Retain the prepared task digest separately; reviewer receives that same identity. Join verifies exact inventory, manifest and bytes, consumer identity and fixed task location. No independent release lookup, mutable local-policy reread or installed-version resolution.
- Receipt includes role, task ID/digest, consumer identity, source full SHA, common bundle and policy/overlay digests. Both roles get identical identities except role. The caller retains receipts externally; joins do not modify the manifest or persist session state.
- Local policy edits and package upgrades cannot replace task bytes. Agreed changes require a new task snapshot; this API has no live rebaseline or upgrade operation. Existing snapshots verify offline without the original package version or release network access.
- Artifact joins and read-only modes do not inject instructions, detect live policy drift, record validation outcomes, prevent snapshot deletion or manage running sessions. Use the separate Git runtime for installed adapters and explicit closure. No manifest field is executed as a product command.

Use `verify_snapshot(task, expected_digest)` for generic offline integrity checks. It checks content, not approval or task-specific context; use `join_task` for role/consumer checks. APIs raise `SnapshotError` for rejected identity/path/policy and may raise `OSError` for filesystem failures. Preserve failures rather than treating missing files/configuration as success.
