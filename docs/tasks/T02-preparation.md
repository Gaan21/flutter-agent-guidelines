# T02 — Exact multi-source preparation

Status: pending. Depends on: T01. Executor: agent in the neutral tool repository.
Read [handoff](README.md), scope, technical-plan sections 1–3 and phase-1 tests.

## Goal

Deliver a non-activating vertical slice: prepare selected bundles from Git, record
one portable selection, restore the same bytes and verify against an independently
retained expected identity. No native connection in this task.

## Work

- Define/test the smallest versioned bundle schema: ID, entry, explicit files and
  notices. Whole self-contained bundles; ordinary local links; no nested modules,
  profiles, source dependency graph or cross-bundle reference protocol.
- Select multiple repositories and several bundles from one source. Directory
  bindings belong in the project selection, not duplicated in bundle metadata.
- Resolve approved channels once per source, then acquire exact commits. An
  explicit exact revision takes precedence. Restore never resolves a branch.
- Preserve source bytes and topology, validate local targets, and leave external
  documentation links untouched. No execution of commands supplied by sources.
- Prepare immutable content off to the side; one portable lock records source,
  bundles, bindings and integrity. Do not embed machine paths or credentials.
- Retain exact prepared bytes/cache for offline restoration. Missing required
  objects produce an actionable error without changing existing selection.
- Establish host task evidence including engine, selection, local policy and
  overlays shared by implementer/reviewer; no session lifecycle manager.

## Acceptance

Use `unittest` with controlled disposable Git fixtures:

- Two sources; multiple bundles sharing one resolved commit; moved branches after
  preparation do not alter restore or review. Count resolver invocations.
- Restore offline into another temporary project root from prepared data; same
  portable identity. Missing cache fails without an implicit network/latest fallback.
- Reject unsafe source/path/ref, link escapes, symlinks/submodules, case collisions,
  undeclared/missing/extra/tampered files, altered inventory/expected identity and
  unsupported schema. Bound inputs without inventing a content interpreter.
- Match role identities; changed engine/policy/overlay is visible as a mismatch.
- Build/install the neutral wheel/sdist cleanly and run relevant checks outside
  checkout. Report macOS/Linux evidence separately.

## Handoff

Document the now-tested CLI/schema and fixture layout, distinguish content from
engine version, and mark T03/T05 ready after review. Preserve expected identity for
review. No claim of installed-client delivery. Completion evidence: pending.
