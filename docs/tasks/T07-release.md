# T07 — Release readiness and authorized publication

Status: pending. Depends on: T06. Executor: release maintainer and owner.
Read [handoff](README.md), scope distribution decisions and prior acceptance records.

## Goal

Make the tested neutral Python package ready for PyPI and versioned releases,
without equating readiness with authorization to publish.

## Readiness

- Confirm `agent-guides` availability/ownership, public repository identity,
  license, notices, engine/content version separation and supported bundle schema.
- Build sdist, then wheel from sdist, inspect exact resources and install/run tests
  outside checkout. Record exact artifacts/digests and supported Python versions.
- Complete real macOS and Linux checks for the advertised support matrix. Missing
  checks block that claim; do not infer one platform from the other's results.
- Provide one tested exact-version installation recipe, first-use prerequisites,
  explicit executable update guidance, content lifecycle commands and recovery.
  No per-consumer installer/probe or unmentioned mandatory package runner.
- Review repository/artifacts for private content, credentials, consumer evidence
  and accidental old-runtime resources. Verify the release matches tested bytes.
- Keep release attestations outside source and preserve independent review inputs.
  A development wheel does not satisfy stable-release artifact task approval.

## Publication boundary

Present artifact versions/digests, checks and remaining limits to the owner.
Staging, commits, tags, pushes, GitHub releases and PyPI publishing each require
explicit authorization; use existing authorized access without configuring global
credentials. Inspect required Git/release state before any authorized publication.

If authorized, publish only the reviewed artifacts and verify clean installation
of the published version. Record public URLs and differences from local evidence.
Do not activate additional consumers as part of publication.

## Handoff

Readiness may be complete while publication is awaiting authorization. Keep both
states explicit; mark the task done only for its authorized agreed outcome.
Completion evidence: pending.
