# Shared guidance delivery: implementation plan

Status: technical proposal aligned with owner decisions, 2026-10-17; no replacement implemented.
[Delivery scope](delivery-scope.md) is the authority for agreed requirements.
Use the [handoff/task index](tasks/README.md) for execution order and progress.
Names, schemas and paths below are proposals, not available commands. Existing
[installed-mode usage](installed-mode.md) remains valid until explicit migration.

## Outcome and session boundary

Build a separate neutral preparation package from the start, reusing reviewed
Python/Git primitives where useful. A single project operation coordinates acquisition,
selection, immutable preparation, native connection and verification. Content
authors retain reading instructions; the executable supplies mechanics only.

One implementation session can deliver the offline prepare/restore/verify vertical
slice in phase 1, with synthetic multi-source fixtures. It cannot honestly finish
transactional integration, both installed-client acceptance and consumer migration.
This design session delivers the plan only. No product sessions or activation are
needed here; later client acceptance requires the consumer agent and permission.

## 1. Reuse map and boundaries

Paths below are relative to this repository. Reuse small primitives behind tests;
do not fork the old runtime wholesale or rewrite working integrity code.

| Existing responsibility | Reuse / change |
| --- | --- |
| `src/flutter_agent_guidelines/snapshots.py`: `canonical`, `digest`, `relative_name`, `checked_path`, `regular_bytes`, `write_snapshot`, `verify_snapshot` | Reuse canonical identities, traversal/link rejection, exact inventories and content-addressed immutable writes. Add composed-selection metadata, bounds and collision tests. A manifest digest alone is not an independent expected identity. |
| `src/flutter_agent_guidelines/git_source.py`: `git`, `validate_source`, `resolve`, `materialize` | Reuse argument-array Git execution, URL/ref validation and tree-mode/blob checks. Split resolution from acquisition: current `materialize` resolves/fetches every time and hardcodes the Flutter allowlist. Exact-ref `resolve` still calls the remote. Add cache-first exact-commit acquisition and manifest-declared files; never call resolution during restore or role join. |
| `src/flutter_agent_guidelines/runtime_io.py`: `save_bytes`, `save_json`, `locked` | Reuse checked, fsynced temporary-file replacement. These are per-file writes, not a multi-file transaction; add durable journal, parent-directory durability where supported, preimage checks and interruption recovery. Existing directory lock has timeout/manual abandoned-lock inspection, not safe automatic stale-lock removal. |
| `src/flutter_agent_guidelines/bundles.py` | Keep legacy packaged export intact. Reuse resource/notices accounting patterns; its fixed payload list and package metadata are not the new bundle schema. |
| `src/flutter_agent_guidelines/installed.py`: `identity`, `pin`, `verify`, `upgrade` | Reuse portable-pin and explicit-update patterns, not its identity unchanged: it binds installed package/payload/profile and deliberately excludes local policy changes. New content identities must be independent of executable releases. |
| `src/flutter_agent_guidelines/installed_installation.py`: `plan`, `verify_connection`, `write`, `uninstall` | Reuse ownership/preimage conflict detection and unrelated-setting preservation tests. Current registrations are hooks/plugins, settings are reserialized, and `write` records intent then writes several files without automatic rollback. Neither its registration nor recovery is the target implementation. |
| `src/flutter_agent_guidelines/policies.py`: `native_policies`, `policy_index` | Reuse local-policy discovery and logical ancestor-scope descriptors as evidence. `policy_index` explicitly is not a selector evaluator; it proves no native loading behavior. Add explicit extra policy/overlay inputs and exclude generated storage. |
| `src/flutter_agent_guidelines/tasks.py`: `local_files`, `prepare_task`, `join_task` | Reuse policy/overlay hashing, shared role identity and tamper tests. Do not require its exclusive task slot, copied product policy tree, release-record format or absolute consumer root for portable selection. Stable-release artifact task approval remains a separate existing contract. |
| `src/flutter_agent_guidelines/deployments.py`, `engine.py` | Reuse ideas for engine-byte fingerprints, not revision-specific executable deployments. Hash executable resources without treating content as engine code. |
| `src/flutter_agent_guidelines/runtime.py`, `bootstrap.py`, `adapters.py`, `installation.py`, `hook_reviews.py`, `adapters/*.js` | Leave legacy lifecycle and adapters operational. No leases, hook injection, guards, end/rebaseline protocol or per-content engine environments in the replacement. Migration detects these registrations; it does not invoke their runtime automatically. |
| `src/flutter_agent_guidelines/cli.py`, `pyproject.toml`, `MANIFEST.in` | Use CLI and distribution tests as patterns for a separate neutral package. Preserve existing commands/resources; the new executable must not depend on the legacy Flutter runtime. Establish its own package metadata and clean-install checks in phase 1. |

Useful test bases: [snapshot tests](../tests/test_snapshots.py),
[installed lifecycle tests](../tests/test_installed_mode.py),
[task identity tests](../tests/test_tasks.py), and
[distribution checker](../tests/check_distribution.py).
The installed test asserting local-policy changes do not change installation
identity is intentional legacy behavior; add new task-evidence tests separately.
[Rulesync evaluation harness](../tests/check_rulesync_trial.py) belongs to legacy
evaluation tooling: its generation/config/cache checks are not a dependency of
the new package or certification of native scope loading.

## 2. Minimal declared content and multi-source selection

Proposed `guidance-bundle.json`, schema 1, at each selected repository-relative
bundle path. Use JSON and Python stdlib, not a new YAML/parser dependency.
Beyond the format version, it declares only `id`, `entry`, `files` and `notices`.
Bundle IDs must be unique within the project selection; no registry is required.

All file paths are bundle-relative POSIX paths. `files` is the explicit inventory
including the entry, local detail and notices; `notices` identifies attribution
files within it. Each bundle is self-contained for local links and installed in
full, but only its short entry is initially loaded; detail is read on demand.
A one-document bundle uses the same format. External links remain links: do not
fetch tutorials or translate them into package dependencies. Reading conditions
live in authored entries next to the guides, never in Python.

The bundle itself is the v1 selection unit: select several bundles when separate
units are needed. There is no `modules`, `requires`, dependency closure or cross-bundle
reference/index schema. Scope/binding is recorded only in the project selection,
not repeated in the bundle declaration. Authored prose still explains applicability.

Proposed portable `guidance.lock.json`, schema 1, contains:

- sources: unique local alias, credential-free Git locator, approval selector
  (normally `refs/heads/develop`) and exact commit;
- selected bundles: source alias, bundle path/ID, bundle snapshot digest and
  binding (`.` for project-wide or a repository-relative directory);
- engine version/byte digest, selected clients and generated integration digest.

Derive selection identity from canonical lock bytes, with machine paths excluded.
Per-file hashes and notices stay in the bundle snapshot manifest, not duplicated
in the lock. One source may supply several bundles, all at its recorded commit.

The lock is the persisted selection; no second project configuration is required
in the MVP. Explicit selection changes produce a new lock through the same
transaction. Keep machine-specific ownership, backups and cache paths in local
state, never in the portable lock. No embedded credentials or private content in
public examples. Private project locks remain in their owner's project.

Resolution rules:

1. Validate owner-selected sources, IDs and paths before fetching. Approval means
   the project-authorized channel/commit, not a trust assertion inferred from Git.
   A project requiring a separate approval artifact must supply its exact commit;
   do not invent an approval service or embed source release attestations.
2. Install/update resolves each selected source once into a candidate record.
   Fetch and confirm that exact commit, then read only declared manifests.
   Multiple bundles from one source share one commit. Restore consumes the lock
   and never resolves a branch. Preserve the candidate across a preview/apply
   boundary: applying the same proposal must not reselect a newer tip.
3. Validate selected bundles and bindings directly. Unknown sources, duplicate
   bundle IDs, incompatible commits for one source and duplicate bundle/binding
   pairs fail before mutation. Different bundles may share or overlap a
   directory binding; do not infer semantic compatibility or choose a prose winner.
   Project decisions and local exceptions remain visible. No automatic activation,
   scope promotion, source-order precedence or fallback to latest.
4. Preserve bundle-relative topology and original bytes under source/bundle
   namespaces. Check selected Markdown links during preparation, not every model
   request: local targets must be declared, present and inside that same bundle.
   Permit ordinary external documentation links without fetching/importing them.
   Reject absolute filesystem links and escapes, including into another bundle;
   validate encoded traversal and ambiguous/case-colliding destinations too.
5. Native bridges name only selected bundle entries, with directory
   labels. Rendered short entries may relocate relative links; retain original
   bytes and hash the deterministic rendition/transform separately. Do not parse
   and inject all detail documents into root context. Hashing selected bytes for
   host verification does not mean loading them into model context.

Internal reuse of identical blobs needs no public protocol. Cross-bundle linking
or dependency features are future work only after a concrete use case establishes
their value; they are not part of phase 1 or required to install common guidance
and project architecture together.

Initial connection selects common guidance plus the separate WorkTracker
architecture bundle where applicable, in one selection. No extra architecture
profile activation. The owner selected the new separate private repository
`worktracker-architecture-guides`; its owner/URL/access and actual content extraction
remain execution inputs. Use synthetic fixtures
until the real source is available and reviewed. Do not publish product content
or relabel the current `profiles/architecture.md` wholesale as WorkTracker.

Before extraction, inventory the source guidance and map every rule, exception,
topic and required reference to its destination, with coverage checks. Ambiguous
common-versus-product content goes to the private WorkTracker bundle by owner
decision. Preserve original source and working delivery until completeness and
consumer migration checks pass; no rule may disappear through classification,
deduplication or rewriting. Retain detailed private migration evidence.

## 3. Storage, identity and transactional operations

Proposed project-local `.guidance/` holds ignored immutable selections keyed by
digest, exact-commit Git objects/cache, generated entries, ownership records and
transaction journals. Prefer project-local storage first; no global settings or
mandatory shared cache. Full source trees and executable source commands are not
materialized. Git submodules, symlinks and executable content are not bundle input.

Retain successful selections; no automatic collection in the MVP. Keep at least
the current and previous version available for recovery. A later explicit prune can
show retained selections for owner review. Retain the exact engine wheel separately: changing
guidance does not install another executable environment. Updating the engine is
an explicit acquisition and project re-verification operation.

The single consumer lock and local recovery state have different responsibilities:

- **Selection lock:** portable, reviewable exact source/content/integration/engine
  identity. It survives removal and restores on another machine without a cache
  path, interpreter location or fresh branch resolution.
- **Ownership journal:** local preimages, after-images and owned blocks/files;
   never the sole expected identity. Store independent backup bytes before writes.

For task identity, the host retains selection/engine identity plus local policy
and overlay path/digest sets and relevant configuration digest once at preparation
for both roles. Reuse its job/review evidence; no second consumer lock, task-state
registry or new lifecycle is required. Discover native policies and accept explicit
extra paths; do not claim arbitrary indirect imports were exhaustively found.
Include local exceptions without globally injecting them.

The host keeps the expected task digest independently of mutable generated files
(for example in its job/review record). Both roles compare that same evidence;
neither resolves latest nor silently recaptures modified policies. Policy drift produces
a mismatch requiring explicit new task preparation between work cycles, not a
lease, mandatory end or rebaseline workflow. Native files remain in place; this
does not enforce a same-user sandbox or guarantee agents read the recorded bytes.

One operation uses these stages:

1. Lock local preparation against concurrent mutation; validate the old lock,
   owned surfaces and absence of conflicting legacy delivery. Inventory only
   selected clients; preserve unrelated guards/lints/settings and local authority.
   Require old/new sessions to be quiescent during connection changes, without
   claiming the tool detects active tasks or manages client sessions.
2. Resolve when allowed; acquire exact objects and all selected bundles, and write a
   new immutable candidate off to the side. Verify it against the candidate
   record. Offline restore uses complete cached objects/prepared bytes; if missing,
   report exact missing identities without altering the active selection.
3. Produce a complete change plan: sources, entries, native owned blocks, lock,
   restart needs, collision/drift findings and retained previous selection.
   A noninteractive apply requires explicit inputs/approval; an interactive
   operation may confirm this plan without an extra configure command.
4. Persist a journal containing transaction ID, old/new identities, preimages,
   intended writes and phase; flush before mutation. Recheck each preimage before
   replacement. Atomically replace individual files, publish lock/activation last,
   verify the connection, then mark committed. No multi-file atomicity claim:
   native files can be partially changed before commit, so no new session starts
   until completion/recovery. Directory fsync guarantees need platform tests.
5. On interruption, the next operation reads the journal first. If bytes match a
   recorded before/after image, deterministically complete or roll back to the
   previous selection; if user edits diverged, stop with exact conflicting paths
   and preserve all bytes. Recovery never overwrites unknown edits. Inspect an
   abandoned lock rather than deleting it based only on elapsed time.

| Operation | Specific behavior |
| --- | --- |
| Install | Take explicit sources/selections/scopes/clients, prepare and connect together; reject unowned collisions. No consumer wrapper or separate registration script. |
| Update | Preserve selections, policy and scope choices; resolve each approved source once, create a new candidate, journal switch, retain old content. Engine acquisition is separate if compatibility requires it. |
| Restore | Require recorded engine identity, lock and exact objects or authenticated access to exact commits. Recreate equivalent integration with local paths excluded from portable identity; do not upgrade schemas or branch tips implicitly. |
| Verify/status | Offline comparison against an explicitly retained expected lock/task digest; validate selected files, generated renditions, registration ownership, engine and policy/overlay/config evidence as applicable. Report version mismatch, do not repair or repin it. |
| Remove | Journal removal of exactly owned blocks/files. Preserve lock, retained versions and unrelated user edits; refuse altered owned material and show manual resolution choices. Restart clients. Cache deletion is a separate explicit cleanup. |

For user-modified files, record exact marker-delimited block bytes and surrounding
preimages. Apply/remove surgically, preserving all outside bytes, newline style
and comments. Changed owned blocks require resolution; unrelated changes can be
rebased by rebuilding the plan from current bytes. Never restore an entire old
settings file over subsequent edits. If JSONC changes prove necessary, stop for
the scoped integration spike rather than add an ad hoc parser or reserialize it.

## 4. Native entry and directory-scope strategy

Preferred candidate: short owned blocks in root and selected-directory native
instruction files, pointing at the prepared authored entries. Claude uses
`CLAUDE.md` with local imports where supported; OpenCode uses `AGENTS.md` with a
short explicit local navigation directive. The directive only connects the entry;
topic-specific reading conditions come from content. Keep existing instructions,
exceptions and native import chains visible; do not add an OpenCode global glob
over every Markdown file or duplicate the same entry via two loaders.

Root entry lists scoped bundle names/locations, not scoped rule bodies. Each
directory bridge connects only the bundles bound to that directory.
Both bridges may target the same immutable content; generated import paths must
resolve from the native file's actual location. Nested-worktree boundaries need
explicit handling. Where existing files already load the target or each other,
inventory/deduplicate before adding a second route.

This is a candidate, not proven native support. Existing hooks/plugins and
Rulesync generation tests do not validate this replacement. Before promising it,
run a bounded spike using two neutral scopes and installed client versions:

- Verify native root discovery from root/subdirectory, import-relative paths,
  nested instruction timing on file reads/edits, ancestor precedence, mixed-scope
  work and nested worktrees. Confirm bridges stay short and detail stays on demand.
- Check existing `AGENTS.md`/`CLAUDE.md` chains, local exceptions and duplicate
  injection; record effective project/user configuration without changing globals.
- Test new session, resumed session and compaction in both clients, including
  interactive TUI. Retain client versions and observed loading evidence.
- If folder loading fails, evaluate one narrow native alternative: Claude's
  path-scoped rules or an installed-version-supported OpenCode directory entry.
  Do not substitute a root all-rules glob. If no native mechanism satisfies the
  scope contract, report the gap before integration; a manual scoped index is
  advisory and does not meet automatic folder-loading acceptance by itself.

No hooks/plugins, injected runtime or per-consumer probes are introduced as a
fallback. The shared tool owns mechanical host checks; the consumer agent supplies
one acceptance record, not a maintained consumer-specific verifier.

Host verification establishes availability, integrity and registration only.
Installed-client observation establishes actual entry/detail loading for those
versions; neither establishes future behavioral compliance or guard coverage.
After any connection/selection change, restart/reload affected clients once and
use fresh task evidence. Already-open contexts retain old instructions; restoring
files cannot retract them. Prepared content remains usable without network or
credentials, and local durable acceptance is distinct from remote acknowledgment.

## 5. Executable location and distribution

Owner-selected: a separate neutral package from the beginning, rather than an
extension of the Flutter-named distribution or a later extraction. Budget its own
metadata, CLI, wheel/sdist resources and clean installation in the first slice.
Reuse audited primitives without importing legacy runtime/content assumptions.
The owner selected a Python package named `agent-guides`, a new public repository
of its own, and PyPI plus versioned releases for distribution. Git provides
acquisition; prefer stdlib mechanics where practical. Check name availability.
Repository owner/local workspace and creation authorization are execution inputs,
not a reason to reopen the selected structure. Publication remains separate.
Standalone platform builds are deferred; they add build/signing/support costs.

For an authorized trial, build an exact wheel and install it in a user-selected
Python environment. Prerequisites are Python 3.11+, Git, build tooling for a source
build, a writable project and authorized Git access for uncached private sources.
One reusable executable installation serves many content revisions. Retain wheel
hashes/bytes; version labels alone are insufficient. No global configuration or
credentials are installed by the tool. PyPI/releases are the selected destination,
not an already published service. Choose and test an exact-version installation
recipe; do not make pipx/uv mandatory without justification. Target macOS and Linux,
test both before claiming support, and explicitly exclude untested Windows support.

Version engine and bundle schema independently; content is pinned by per-source
commit and bundle digests. Unsupported schema fails before mutation. A content
update compatible with the schema never requires a new engine environment.
Owner-approved development Git trials remain possible; they do not become stable
release attestations or satisfy existing artifact-task release approval rules.

## 6. Executable phases and checkpoints

Every implementation session starts by checking status/diff and this scope, then
records delivered behavior, test results, limitations and the next checkpoint.
Changes to existing usage documentation wait for an explicit migration release.

| Phase | Deliverable and acceptance gate | Where |
| --- | --- | --- |
| 0 — this design | Reuse map, proposed records, transaction model, client spike and bounded owner decisions. Local links and diff hygiene checked. | Here; design only. |
| 1 — first implementation session | Minimal bundle validation plus prepare/restore/verify through a proposed non-activating CLI path; two synthetic Git sources, several bundles from one source, exact commits, one portable lock, immutable cache and independent expected digest. Install whole self-contained bundles and preserve local detail links. Restore offline to a second temporary root after source branches move; tamper/escape failures leave existing selection untouched. No native connection or cross-bundle features yet. | Repository agent; next authorized session. |
| 2 — native feasibility | Shared minimal fixtures and acceptance matrix for both clients; root/two scopes, local authority, relative detail, no duplication, restart/resume/compaction and TUI. Select one supported bridge mechanism per client or stop with evidence. Can run independently after record/layout stabilization. | Consumer agent with installed clients; no private content needed. |
| 3 — complete lifecycle | Journaled install/update/remove and restore connection using phase-2 mechanisms. Fault injection at every publication step; idempotent recovery, preserved user edits, old-version retention and engine/content compatibility checks. One operation includes connection and verification. | Repository tests here later; installed-client confirmation by consumer agent. |
| 4 — explicit migration | Separate reviewed common/project bundles, owner-selected private source, approved legacy disconnection plan, full measured lifecycle and rollout/rollback record. Old guard `apply_patch` coverage fixed/tested independently by its owner. | Consumer agent and owner; never automatic. |

Required `unittest` evidence in phases 1/3:

- Multi-source resolve-once counting, shared commit for bundles from one source,
  branch movement between preview/apply and roles, exact restore with no resolver
  or network call on a complete cache, missing cache fails without switching.
- Whole-bundle installation, entry-only initial loading (observed in phase 2),
  preserved local detail links, external links left untouched and directory
  bindings recorded only in the single project lock.
- Duplicate IDs/bindings, unknown source, missing local link targets, unsafe
  URL/ref, absolute/traversal/encoded links, Git symlink/submodule/tree-mode attacks,
  filesystem symlink ancestors, case collisions, missing/extra/tampered files and
  manifest/expected-digest tampering. Bound manifest size/file count/input bytes.
- Same implementer/reviewer source, bundle, selection, engine, policy and overlay
  digests; changed local exceptions/config/engine fail comparison. Evidence is
  portable across temporary roots without copying private paths into public data.
- Concurrent writers, interruption/retry at each journal phase, crash after a
  native-file replacement but before lock publication, unrelated user edits,
  altered owned blocks, no-op install and remove/update/rollback idempotence.
- Adapt the existing distribution-check pattern for the neutral package: build wheel **from sdist**, inspect
  exact resources/notices and new schemas/templates, install cleanly, run CLI and
  unittest outside the checkout. Keep legacy resource and API regressions green.
  No consumer commands, network credentials or product services in unit tests.

Run targeted tests first, then distribution/clean-install acceptance when code and
resources change. No runtime tests are necessary for this document-only session.
Report only platforms/client versions actually exercised. Two temporary roots
test portability; they do not prove a second physical machine or another OS.

## 7. Execution inputs and design risks

The architecture source decision is settled: a new separate private Git repository,
named `worktracker-architecture-guides`, preserving all guidance and assigning
ambiguous rules to WorkTracker. Its owner/URL/access/creation authorization and
reviewed extraction are migration prerequisites, not phase-1 blockers.

The executable decision is settled: `agent-guides`, a neutral Python package in
its own new public repository, distributed via PyPI/releases, targeting macOS and
Linux. Only availability, owner/workspace/access and action authorization remain
to be checked. Do not reopen these product choices as implementation preferences.
A local wheel trial validates development before explicitly authorized publication.

Reversible implementer choices: provisional filenames/CLI spelling, Python module
layout, limits, journal encoding and explicit retention beyond current/previous.
Choose these with tests; do not reopen Git-only, multirepo selection, native entry,
authored navigation, no extra architecture activation or Rulesync decisions.

Real uncertainties: installed-client scope/import behavior, private content split,
availability of exact Git objects for later restore, and crash durability on other
platforms. Retain prepared selections and wheels; a lock cannot make a deleted
remote commit retrievable. Neither hashes nor host verification prove trust or
model compliance. A live snapshot is never overwritten; changes wait between
work/review cycles without introducing a session lifecycle manager.

Avoid turning the MVP into AI retrieval, a daemon, a generic plugin system,
Markdown interpreter, own guard framework or per-content runtime deployments.
Nested module selection and cross-bundle dependency/reference machinery are also
outside v1; the self-contained bundle and one project lock are sufficient.
No incompatible agreed requirements were found. Automatic folder loading remains
a feasibility gate, not a promise; failed installed-version tests must surface the
gap before claiming the complete native integration works.
