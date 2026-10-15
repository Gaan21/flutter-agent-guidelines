# Implementation and verification procedures

Packaged procedures specify work and evidence, not installed commands.

## Start and route

1. Read consumer authority and task preloads. Confirm common-content and private-overlay identity against the same manifest used by review; no independent latest lookup.
2. Identify changed boundary and owners. For data/error/time/UI work read [boundaries](../decisions/boundaries.md); for lifecycle/async/offline read [reliability](../decisions/reliability.md).
3. Read the relevant consumer API/decision and inspect installed interfaces. Record conflicts or missing contracts before affected implementation. Use [upstream references](../references/upstream.md) only for the unresolved topic.
4. Select a bounded patch and approved validation commands for an explicit consumer/package root. Preserve local scope limits and checkpoints. This guide supplies no activated hooks or generic shell gate.
5. Implement one responsibility at a time; verify changed behavior at the simplest sufficient test layer. Keep snippets small; use actual shared components instead of cloning tutorial implementations.

## Behavior and risk checklist

Select applicable cases and record why others do not apply. This guidance sets no universal counts, ratios or coverage thresholds; changing an existing consumer baseline still requires approval.

- Data: create/update identity, missing/malformed fields, pure mapping/default ownership, codec round trips, server rejection, stack/context preservation and visible failure.
- State/actions: initial/loading/data/empty/error, ordered one-shot effects, duplicate invocation, stale response, navigation before completion and post-disposal events.
- Ownership: borrowed vs owned cleanup, parent/helper teardown, inferred/multiple resource fields, early return and conditional paths; overlay close/rebuild/caller removal.
- Composition: correct factory/singleton lifetimes, disposal, real routing/deep links/back/pop interception, tab state and contextual actions; list identity after reorder.
- Time/copy: fixed time seam, instant/civil serialization, device/business-zone differences, midnight/DST, translated error codes and placeholders.
- Offline/auth, when applicable: pending restart/merge/delete acknowledgment, rollback/skew, reconnect, single refresh, retry budget/cancellation and status visibility.
- Diagnostics: one report across layers, approved technical events, nested/dynamic redaction and remote sink policy.
- Regression selection: meaningful visual and DI checks are legitimate risks. Generated code/trivial getters need no ritual tests; cover their meaningful boundary behavior where relevant.

Use deterministic doubles/time for isolated tests. Real router or in-memory database collaboration may warrant integration coverage; classify effects explicitly. Install listeners before actions, bound waits, reset shared fixtures and dispose resources. Review runtime and redundancy rather than omitting distinct risks to fit a test cap. Golden baselines need a stable environment and reviewed differences; no blanket retrofit required.

Run an E2E matrix only on explicit user request, using the verified consumer harness, fixtures, bounded waits and cleanup/post-check contract. Do not infer platform/driver support from a generic tutorial.

## Control evidence

For each obligation record separately:

| Evidence | Required record |
|---|---|
| Availability | Package name, full source revision/resolved version, SDK compatibility |
| Predicate | Actual diagnostic name, scope, exceptions and known misses/false positives |
| Registration | Constructor/plugin actually registered; source presence is insufficient |
| Consumer configuration | Dependency/lock and configuration hashes, include chain, enabled rules, severity and exclusions |
| Execution | Explicit package root, command/arguments, exit status, tool output and valid/invalid cases |
| Residual protection | Types/components, behavior tests, review, owner and unresolved gaps |

Keep separate records for separate lint packages and consumers. Partial upstream configuration lists do not prove release equality, missing-rule absence or installed activation. Do not enable nonexistent/disabled names from a template.

Standard async-gap context checks cover the guarded context after await; they do not establish overlay ownership. Print checks do not establish redaction. An annotation cannot prove deep immutability; a key argument cannot prove stable identity; a reason tag cannot prove safe background work. Sink checks have detection limitations and need consumer evidence before replacing cleanup instructions.

Verify a gate using clean input, known violation, crash, missing SDK/config/package, unrelated diagnostics, generated paths and no-touched cases. Preserve subprocess failures; filtering output to no matches cannot convert failure into success. Missing required configuration is an error, not a clean pass.

## Close and maintain

- Run approved checkpoints/final commands and relevant tests. Report passed, failed, skipped and not-run separately, with scope and reasons. Analyzer success is not proof of product correctness.
- Use locked toolchains; generation only when required. Never infer an upgrade requirement from a documentation page's SDK label.
- Review semantic names, cohesion and boundary direction. Formatter output does not settle architecture or API conventions. Declaration-sensitive style changes require approved consumer policy and installed-control evidence; resource-field typing remains protected until cleanup detection is sufficient.
- Record exceptions, approval, covering evidence and recovery obligations required by the consumer. Do not add suppressions/exclusions as a default fix.
- Return exact changed files, checks, unresolved contracts and residual risk to review under the same manifest. Propose shared changes separately; no snapshot edits, automatic Git actions or publication.
- Maintain concise English, file/section citations and per-file provenance. Link upstream instead of copying tutorials; preserve upstream recommendation strength. Historical status and efficacy claims need evidence.
