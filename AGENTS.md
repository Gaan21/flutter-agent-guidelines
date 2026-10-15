# Maintainer instructions

- Scope: this repository's Python tooling and original Flutter guidance. Consumer entry: `src/flutter_agent_guidelines/payload/AGENTS.md`; keep maintainer policy separate.
- English; concise. Files below 500 lines. One canonical payload; no private paths, source reports, internal revision pins or product APIs in public content.
- Task identity locked at preparation: same source revision, bundle and policy/overlay digests for implementer and reviewer. Never resolve latest independently or edit a live snapshot.
- Hashes establish integrity, not publisher trust. Development builds cannot prepare approved operational tasks. Keep release attestations outside source.
- No automatic staging, commits, pushes, releases, registry publishing or consumer activation. Each requires explicit user authorization.
- No native runtime enforcement claimed without installed-version tests. No implicit hooks, global configuration, credentials or product-command execution.
- Verify wheel/sdist resources, clean installation, tamper/path rejection and task identity with `unittest`. Test only supported runtimes actually available; report platform limits.
- Preserve upstream modality and offline durable-local acceptance versus remote acknowledgment. Link third parties; do not import their tutorials, configurations or lint sources.
