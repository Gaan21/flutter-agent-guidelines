# Automatic updates at work boundaries

Configure each consumer worktree once with `--auto-update`. Compatible future work
uses the latest successfully resolved commit of the approved channel, including
Python, adapters and guidance. Open work remains pinned. A registry release is not
required for owner-approved Git trials.

## Responsibilities and boundaries

| Layer | Responsibility |
|---|---|
| Discovery | Resolve the approved ref before new work; report `UPDATE` or `UNKNOWN` during existing work. Never interpret discovery as activation. |
| Guidance | Copy the selected revision's allowlisted Markdown/notices into the work snapshot. |
| Python controller | Prepare a self-contained, dependency-free source installation per revision in the external cache. Run it in a fresh isolated interpreter. |
| Native connection | Keep installed Claude command hooks and the OpenCode transport plugin stable. |
| Versioned adapters | Execute the selected Python hook implementation; OpenCode dynamically imports that work's verified JavaScript hook implementation. |
| Work lifecycle | Create only when no work is active; continue the existing identity until explicit acceptance/closure and release of all leases. |

The installed bootstrap is deliberately small and fixed. It is not a self-updating
`pip` environment. Deployment packages include standard version metadata and license
resources, but do not execute `setup.py`, build backends or dependency installers.
Protocol 1 supports the current pure-Python, dependency-free package layout. A new
dependency, unsupported Python requirement or incompatible contract needs explicit
migration rather than silently installing from another registry.

### What the owner approves

```sh
flutter-guidelines configure --repo "$PROJECT" \
  --source-url https://github.com/Gaan21/flutter-agent-guidelines.git \
  --source-ref refs/heads/develop --auto-update
flutter-guidelines configure --repo "$PROJECT" \
  --source-url https://github.com/Gaan21/flutter-agent-guidelines.git \
  --source-ref refs/heads/develop --auto-update --apply
flutter-guidelines install --repo "$PROJECT"
flutter-guidelines install --repo "$PROJECT" --apply
```

Review both plans first. `--auto-update` authorizes execution of future compatible
code from this exact source, not merely reading its documentation. A hash establishes
integrity, not publisher trust. Git requests disable credential prompts, user/global
Git configuration, hooks and HTTP redirects. Only the approved source is fetched.
Production configuration requires HTTPS; local Git fixtures are test-only sources.

Keep the bootstrap's tools environment and Python executable in place. Do not upgrade
that environment in place while consumers use it. The source revision used for new
work must contain the protocol-1 contract and engine; older content-only revisions
cannot be used as automatic executable deployments.

## Exactly when a work starts or continues

- The first session callback in a worktree with no active work prepares a controller
  and creates a new identity. Opening a client with no conversation need not do so.
- Every additional conversation, resumed session and reviewer joins the active work,
  including its controller, adapters, common revision and local-policy snapshot.
- A fresh conversation does **not** implicitly finish previous work. Use `end` only
  after acceptance; the last session release archives the closing record.
- Closing work refuses new participants. Existing sessions retain their leases and
  can finish; neither discovery nor preparation releases them.
- A native session previously bound to an archived identity cannot silently start a
  new work. Start a new native conversation after archival. Bindings survive restart.
- Rebaseline remains human-owned, requires all leases released and preserves the
  old controller/common revision. Review and implementation must renew validation
  against the replacement identity in fresh participating conversations.

There is one work slot per physical consumer worktree. Concurrent independent work
requires separate configured worktrees or consumer roots. Their controllers can
share the external cache while remaining pinned to different revisions. No intent,
idle-time or response-completion heuristic closes a work.

## Preparation, concurrency and failure

1. The stable dispatcher serializes selection and work creation per consumer.
2. For moving refs it resolves the channel once to a full commit; fetches use that
   exact commit. Fixed refs use their known full SHA.
3. A shared-cache lock serializes deployment publication. Files are read from Git
   objects with regular-file checks; controller syntax, metadata, protocol and an
   isolated engine probe must succeed before publication.
4. Preparation uses an unreferenced staging directory. The completed content-addressed
   installation is renamed into place, then indexed atomically. A pointer is saved
   before the selected controller creates the work. A pointer without active work
   does not pin the next attempt: moving refs are resolved again.
5. Each dispatch verifies the retained deployment and installed connection. Work
   joins additionally verify snapshot, controller, policies, configuration and leases.

A failed channel lookup or preparation leaves conversation available with a warning,
without new verified work or guideline injection. If a controller was previously
selected, the warning labels it **last-known**, with freshness `UNKNOWN`; it does not
claim to run latest. A subsequent callback retries preparation.

An existing work resumes offline using its verified deployment/snapshot. Failed
update checks report `UNKNOWN`. For new work, a cached exact fixed revision can be
used offline; a moving ref requires successful resolution even if its previous
deployment is cached. No stale fallback is silently labeled current.

Published installations are retained: there is no automatic garbage collection or
replacement of versions used by other worktrees. Interrupted staging directories
are not active versions. If a process dies while holding a directory lock, inspect
the corresponding `lock` directory and confirm its owner has exited before removing
that abandoned lock. Never remove live leases, deployments, snapshots or work records
to clear an update problem. Corrupt published deployments fail verification and
require operator inspection; they are not overwritten as a repair shortcut.

## Pin or roll back future work

Use a real full commit already approved by the owner in place of `$KNOWN_SHA`:

```sh
flutter-guidelines track --repo "$PROJECT" --source-ref "$KNOWN_SHA"
flutter-guidelines track --repo "$PROJECT" --source-ref "$KNOWN_SHA" --apply
```

To resume channel following:

```sh
flutter-guidelines track --repo "$PROJECT" --source-ref refs/heads/develop --apply
```

This writes only ignored `.flutter-guidelines/future-source.json`. It changes neither
versioned configuration nor the active identity. It can select only a ref of the
already approved URL. A source URL change requires explicit reconfiguration after
closure and uninstall. A newly selected incompatible revision fails preparation;
select a known protocol-compatible revision or perform the migration below.

## Migrate an existing Git installation

This is a one-time maintenance operation, with owner approval. Preserve application
edits and approved guards. Do not run it from a session that still holds a live lease.

1. Using the **old installed CLI**, inspect `status`; finish/review/accept the current
   work, call `end`, then exit all participating sessions. Inspect remaining leases
   from an ordinary terminal; use `release` only for sessions confirmed exited.
2. Preview and apply `uninstall` with that same old CLI. Keep its environment until
   restoration succeeds. Modified owned files require inspecting its retained backups.
3. Build/install this package in a **separate tools environment**, using the README
   installation commands. Preserve the old environment for recovery. Once approved
   source contains this implementation, it can serve as the automatic-update channel.
4. With the new CLI, run the configure plans above, retaining every existing
   `--policy`, `--overlay`, `--cache` choice and reviewed guard approval. Reconfiguration
   is permitted only with no work and no installed connection. Existing guard reviews
   are retained and checked; changed guards need separate explicit review.
5. Apply installation, quit and restart the selected clients. Use the README's
   connection check in a **new native conversation** and compare the work's exact
   revision/controller identity with `status`.

If the old configuration was edited in advance to a different revision while its
old controller/work remains active, stop the migration. Inspect the old work's
original configuration and installation evidence; restore only the owner-approved
matching configuration before using the old closure/uninstall path. Do not upgrade
the old environment, copy a new controller identity into state or overwrite an active
snapshot to bypass a mismatch. Pending application edits are not migration inputs
to discard. Recovery must be performed separately with that consumer's owner.

### Future transparent updates and exceptions

Normal compatible Python, JavaScript adapter and Markdown updates require no consumer
commits, SHA edits or reinstall. The stable transport chooses implementations per
work; a running OpenCode client is not asked to reload its installed plugin file.

Installing or changing the stable connection, bootstrap protocol, Python executable
or native hook event contract requires closing affected work and reinstalling the
connection from a new tools environment, followed by client restart. On incompatibility,
the warning stops new verified preparation; `track` to a known compatible revision
restores future preparation while an explicit bootstrap migration is arranged.

## Factory integration boundary

The local factory material inspected for this change describes coordinator-owned,
read-only instruction delivery to isolated workers and reviewers. No executable
integration with this public runtime or agreed lifecycle/receipt mapping was found.
Its native workers cannot be assumed to discover consumer-local hooks or reach the
host cache. **Factory integration is therefore not supported or activated here.**

Required follow-up contract: the coordinator selects the approved source once at
task preparation, retains the exact executable/content/policy identity, delivers
read-only material to workers, gives the same identity to reviewers, records actual
lease/closure semantics and defines network/cache access outside worker permissions.
It must also define how task approval and this runtime's work slot correspond. The
separate stable-release [artifact task API](task-api.md) is unchanged; these Git
deployments are not artifact release attestations. No factory repository was changed.

## Evidence and real-client checks

Automated `unittest` tests use local trusted Git fixtures and actual isolated Python
controller processes. Direct Node hook tests exercise the stable dispatcher and
versioned adapter loading, context replacement, guards and independent leases.
Distribution checks build wheel/sdist, compare packaged resources and run all tests
from a clean installed wheel outside the source tree.

Still required in real Claude Code and OpenCode installations: first callback order,
public injection, native folder scope, multiple live clients, resume/compact, reviewer
join, fresh work after archival, native release/deletion/exit delivery, crash recovery,
warning visibility and incompatible-bootstrap recovery. OpenCode `dispose` is tested
only as a directly callable hook; native invocation is not established. Claude's
parent-process lease assumptions also require native validation. Other operating
systems and the declared minimum Python version have not been tested for this change.
