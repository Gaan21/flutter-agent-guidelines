# T04 — Complete lifecycle and recovery

Status: pending. Depends on: T02 + T03. Executor: neutral tool agent.
Read [handoff](README.md), technical-plan sections 3–4 and T03 evidence.

## Goal

Implement complete install/update/restore/status/verify/remove operations using
the tested native mechanisms, without a consumer-owned wrapper or probe.

## Work

- One operation performs preparation, connection and verification. Preview may be
  available but is not a mandatory separate configure/install sequence. Applying
  a retained proposal never re-resolves source tips.
- Persist confirmed bundle/client/scope selection. Routine updates preserve local
  exceptions and lint choices, and do not reinstall a compatible executable.
- Inventory only selected clients; preserve local instruction authority, user
  configuration/comments and unrelated guards. Detect competing legacy loaders.
- Track owned files/blocks, before/after bytes and a durable transaction journal;
  recheck preimages, publish activation last and retain working selections.
- Recover interrupted operations without overwriting unknown edits. Multi-file
  changes are not an atomic transaction merely because each file uses rename.
- Remove only owned integration; preserve unrelated edits and recorded selections.
  Modified owned material needs explicit resolution. No silent cache deletion.
- Verification is offline comparison against retained expected identity, not an
  implicit repair, source refresh or policy rebaseline.
- Report restart/reload needs. No live snapshot rewrite or hot-context guarantees.

## Acceptance

`unittest` covers complete lifecycle, no-ops, concurrent preparation, faults at
every write/publication stage, restart/retry, altered owned blocks, unrelated user
edits, changed content updates, retained-version recovery and exact restores.
Check engine/schema mismatches, root/scoped registration and source/link integrity.
Prove preservation of user bytes, not only equivalent parsed settings.

Run distribution/clean-install checks and macOS/Linux tests for supported behavior.
Repeat installed-client checks when the implementation changes T03's mechanism.
Measure every required setup/update/restore/removal step, including initial Python/
Git/tool acquisition. A wrapper hiding many required configurations is not success.

## Handoff

Record one documented usage path and tested commands. Mark T06 ready only after
T05 also passes. Do not migrate existing consumers in this task.
Completion evidence: pending.
