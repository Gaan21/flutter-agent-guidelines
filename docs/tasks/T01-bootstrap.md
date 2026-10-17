# T01 — Bootstrap agent-guides

Status: ready. Depends on: none. Executor: repository agent.
Read [handoff](README.md), [scope](../delivery-scope.md), technical-plan sections 1/5.

## Goal

Establish a separate neutral Python package in a new public repository without
coupling it to the current Flutter runtime. This is scaffolding, not installation
of guidance into a consumer.

## Execution inputs

- Actual repository owner, approved local workspace and authorization for any
  repository creation. Do not infer an account, parent directory or remote URL.
- Read-only checks of `agent-guides` repository/PyPI name availability. If occupied
  incompatibly, report the conflict and ask for a name decision; do not substitute.
- A supported available Python/Git runtime and an identified Linux validation path.
  Publication credentials are not required for this task.

## Work

1. Create the authorized repository/package scaffold, with neutral CLI/module
   naming, Python compatibility declaration, license/notices and test/build setup.
2. Establish maintainer instructions preserving integrity, privacy, authorization
   and native-loading limits from this repository without Flutter-specific runtime
   assumptions. Reuse audited code only with its required license/provenance.
3. Provide a minimal CLI identity/help path. Do not implement command-shaped stubs
   that report success for install/update/verify before those operations exist.
4. Carry the canonical handoff to the new repository per the index; repair links
   to legacy reference code and leave a single authoritative task board.

## Acceptance

- Build sdist and wheel from sdist, inspect expected resources/notices, install
  into a clean tools environment, and exercise CLI help/version outside checkout.
- No Flutter payload/runtime dependency and no consumer changes/global settings.
- Record available Python/OS checks; Linux remains pending if not exercised.
- Record actual repository/handoff locations without placing private paths in
  public documentation. No publication implied by a working package build.

## Handoff

Mark T02 ready after review. Record package structure, exact check commands/results
and code-reuse decisions. Repository creation/publication permissions remain
separate from implementation permission. Completion evidence: pending.
