# Changelog

## Unreleased — 2026-10-15

- Clarify shared guidance, folder-local instructions and executable project checks;
  add initial connection checks, runtime terminology and package-release boundaries.
- Update validation status with the reported initial real-project OpenCode trial,
  distinguishing earlier adapter behavior from pending lifecycle and recovery checks.
- Continue prompt/start processing without injection when runtime verification or
  OpenCode invocation fails; show Claude system warnings or OpenCode warning toasts.
- Run protected-state guards before verification and retain an OpenCode local guard
  during controller failure. Ordinary reads and edits remain available.
- Mark local-policy drift as `rebaseline-required`; block closure until explicit
  human preparation. Add plan/apply `rebaseline`, preserving common-source revision
  while replacing local-policy, work and snapshot identity after lease release.
- Document dedicated read tools for protected paths; shell commands stay
  conservatively guarded without a read-only shell parser.
- Add concise dialog-result ordering, single-owner form exit, deferred initial
  loading, shared load/refresh completion and deterministic widget-test guidance.
