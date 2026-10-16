# Flutter engineering: common entry

Flutter guidance for developers and agents. Installed adapters verify pinned content;
written engineering rules are not analyzer or operating-system enforcement.

## Authority and task identity

- Read consumer authority and concrete task preloads first. Consumer security, ownership and approved architecture govern implementation.
- Implementation and review use the same project revision and verified guidance identity. Installed-version delivery uses the project pin and its selected profiles; it does not require work leases, `end` or policy rebaseline. Package updates are explicit, between review cycles, with affected contexts reloaded. A cache path or version label alone is not an identity.
- Artifact-task and legacy work delivery retain their manifest contract: common revision/bundle, consumer and policy/overlay hashes, toolchain/configuration and role joins. Review joins that manifest without independently resolving latest. Explicit rebaseline applies only to delivery modes that snapshot local policy. Never replace live snapshot bytes.
- Load the relevant decision below, then its applicable procedure. Stop reference traversal once the decision is resolved. Missing required consumer contracts block only affected implementation; record the gap rather than inventing APIs.
- Preserve installed interfaces. Common recommendations do not authorize relaxing an existing consumer rule, suppression, test baseline or operational limit.

## Working boundaries

- [Engineering boundaries](decisions/boundaries.md): data/serialization, failure visibility, dependency lifetimes, immutable values, time, UI state/effects, identity and localization.
- [Reliability](decisions/reliability.md): owned resources, overlays, critical completion, concurrency, retries and conditional offline behavior.
- [Verification procedures](procedures/verification.md): scoped workflow, behavioral checklist, control evidence and truthful closeout.
- [Selected architecture profile](profiles/architecture.md): read when selected by the project connection or local authority; strict names/member order, selective typing and the matching lint selection. Availability alone does not activate it.
- [Upstream index](references/upstream.md): optional topic references; no recursive required reading.

Prefer clear responsibilities and explicit boundary conversions. Choose domain layers, usecases, code generators and containers according to the consumer architecture. No universal base hierarchy, storage protocol or component API is prescribed here.

Identify owners before editing: state, disposable resources, ephemeral effects, failure reporting, background work, retries and acknowledgment. Await critical completion; distinguish replacement reads from nonrepeatable writes. Keep sensitive values out of diagnostics and technical errors out of user copy.

Use deterministic time seams; distinguish instants, civil dates and display zones. Never infer a company timezone or a synchronization protocol from generic examples.

Inspect effective controls and approved commands before claiming enforcement. A source file, configuration name or written fixture is not an executed control. Test behavior and failure risks; this guidance sets no universal test maxima or pyramid quotas. Existing consumer requirements remain authoritative until separately changed.

## Change authority

- Suppressions/exclusions require explicit approval and traceable justification. Preserve stricter consumer exception/recovery requirements.
- Sensitive Git, release, deploy and runtime activation actions require explicit authorization. Guidance installation alone does not activate hooks or plugins.
- Propose shared-rule changes separately; never edit a live task snapshot. Keep historical material separate from current authority.
