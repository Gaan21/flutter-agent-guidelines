# agent-guides: agreed delivery scope

Status: owner decisions consolidated, 2026-10-17. Direction selected: Git
acquisition and native Claude Code/OpenCode loading with `agent-guides`.
The replacement is not implemented. Current installation and migration commands
remain documented in [installed mode](installed-mode.md).
Execution starts at the [agent handoff and task index](tasks/README.md).

## Purpose

Make selected Markdown guidance available to both clients with a short initial
entry and detailed documents read when relevant. One shared tool prepares the
content and integration; consumers should not maintain installers or probes.
Adding a technology should primarily mean authoring guidance, not another runtime.

The tool manages availability, selection, versions and placement. Authors supply
the meaning: what applies always, when each topic is needed, and its scope. Native
clients load the initial entry and local folder instructions; agents follow the
entry's directions to consult relevant detail. File placement alone cannot ensure
that an agent consults every relevant document or follows every instruction.

## Decisions carried forward

- Use Git and native loaders as the base. Rulesync is not the default dependency.
- Installation and explicit updates select the latest approved `develop` commit
  once, unless an exact revision or another project-approved policy is requested.
- Record that exact commit automatically. Startup and upstream pushes do not
  change the selection. Prepare updates between implementation/review cycles.
- Preserve product instructions, local exceptions, hooks and guards. Common
  guidance does not silently change architecture or executable lint selection.
- Keep content and the delivery executable separately versioned. Guidance updates
  should not require changing the tool when the content format remains compatible.
- Build a neutral, stack-agnostic executable package from the start, rather than
  extending the Flutter-named distribution or deferring extraction. Reuse reviewed
  primitives where useful without requiring the legacy Flutter runtime. Package
  name is `agent-guides`, in a new public repository of its own. Check name
  availability before scaffolding; do not silently substitute another name.
- Distribute a Python package through PyPI and versioned releases. Development
  wheels/exact Git trials precede stable publication; a standalone executable is
  outside v1. Repository creation and publication need separate authorization.
- Target macOS and Linux in v1; verify both before claiming support. Windows is
  deferred. Python/Git installation prerequisites must be explicit.
- Support both clients with local prepared files and no delivery hooks, leases,
  mandatory `end`, or executable environment per content revision.
- Installation should be one operation plus at most one restart per selected
  client. Updates should be one explicit operation. Account for first-use tool
  acquisition and prerequisites rather than hiding them in command counts.

## First-version inputs

Owner-confirmed: support multiple Git source repositories per project, Git-only
acquisition initially, and reading/navigation instructions maintained alongside
the guidance rather than embedded in the tool. One source can still contain
multiple bundles. Local-folder import is deferred.

Use a small declared guidance bundle rather than trying to interpret arbitrary
Markdown automatically. A bundle contains:

- A short entry naming the general requirements and explaining which documents
  to consult for which work.
- Topic documents, with ordinary relative links and their required dependencies.
- A small machine-readable declaration with bundle ID, entry, explicit file
  inventory and notices. Bundles are self-contained; nested module selection and
  cross-bundle dependency machinery are outside v1. The replacement does
  not require a separate architecture-profile activation; current installed-mode
  profiles remain part of the existing implementation until explicit migration.
- Required notices and attribution, kept with the content.

Each source is a Git repository with a declared bundle path and an exact recorded
commit. Installation/update resolves approved sources once during preparation;
implementation and review reuse that prepared selection. The tool must not
independently resolve branches for each role.

An individual `.md` file could be a one-document bundle, but its role and scope
must still be specified. Importing a large file does not automatically split it,
write a useful index or infer when its sections are relevant. Loose-file import
and automatic content restructuring are not assumed first-version requirements.

A source repository must be selected by the owner/project. Discovery may suggest
bundles and directory scopes; activation requires confirmation and persistence.
Record one exact revision per selected source, with its selected bundles, as one
project identity. Independently versioned modules within one source and automatic
technology detection are not selected features.

### Architecture organization — owner-selected

Keep common guidance separate from a specific bundle named **WorkTracker
architecture**. The project's initial connection includes both; routine startup
and updates preserve that selection without requiring another profile activation.
This bundle is project-specific, not a generic architecture default for unrelated
consumers. The owner selected a new, separate private Git repository for this
bundle, named `worktracker-architecture-guides`. Its owner/URL, access and creation
authorization are execution prerequisites; the privacy/name decision is closed.

Project-local instructions and exceptions retain authority. Bundling WorkTracker
architecture does not authorize copying private product details into the public
common guidance repository. The current `architecture` profile is not
automatically renamed or reclassified: its reusable conventions and any actual
WorkTracker-specific decisions need review when preparing the separate bundles.

Content preservation is mandatory: inventory the existing guidance and map every
rule, exception, topic and required reference to its destination. If common versus
WorkTracker classification is uncertain, retain it in the private WorkTracker
bundle. Do not drop or weaken it during extraction. Preserve the original source
and check completeness before retiring old delivery; source deletion is not proof
of successful migration. Keep the detailed classification record private.

## Proposed operations

Names below describe responsibilities, not a finalized CLI.

| Operation | Responsibility |
| --- | --- |
| Install | Select sources/bundles/scopes and clients; resolve once; prepare local content; register short native entries; verify; report restart needs. |
| Update | Preserve selections and local decisions; resolve the approved new revision once; prepare and verify separately; switch to it with a recovery path. |
| Restore | On another machine, prepare the project-recorded exact revision and selection, not the current branch tip. |
| Status / verify | Report the selected identity and compare content, entries and owned registration against an independently retained expected identity. |
| Remove | Remove owned entries/registrations without deleting unrelated settings or instructions; handle modified owned files explicitly. |

The tool should absorb repeated mechanics. Consumers keep a portable selection
record and the native connection, not custom installer scripts or an additional
consumer-specific verifier. Python packaging and PyPI/releases are selected;
command spelling, file layout and storage/rollback retention are technical details.

## Context behavior

1. At startup, load a concise entry for the selected bundles, not all topic files.
2. The entry identifies the installed selection, source and local topic paths. It
   tells the agent what must be read before applicable work, without duplicating
   the full guidance in every client.
3. Keep detailed topics available locally, including linked dependencies. Preserve
   links or record any necessary entry transformation separately from source bytes.
4. Directory selections must apply only within their declared scopes. A root
   index may name scoped bundles without injecting their full rules globally.
5. Keep native root/folder product authority and explicit local exceptions visible.

For example, a future mixed repository could select Flutter for `mobile/` and a
web bundle for `web/`. The entry provides navigation; work in `mobile/` should
trigger the Flutter documents, not a full web handbook. Flutter is the existing
content; this example does not claim a web bundle exists.

This is indexed, on-demand reading. Automatic semantic retrieval, model-driven
summarization and a running context-selection server are not part of this proposal.
Test actual client loading and topic discovery separately from behavioral compliance.

## Integrity and lifecycle boundaries

Prepare files locally before agents start. Verify content, generated entries and
owned configuration; a Git content SHA alone does not cover the integration.
For automated tasks the host retains engine identity, source revision, selection,
local policy and overlay digests once for both implementer and reviewer. Local
product instructions remain native; retaining task evidence does not require
rewriting or freezing all product files into global always-on instructions.

Prepared guidance should remain available when agent commands have no network or
credentials. Hashes establish integrity, not publisher trust or model compliance.
Prepare new versions separately, preserve a working version on failure, and do
not rewrite a snapshot used by an active task. Existing sessions retain delivered
instructions until contexts are reloaded; do not promise hot replacement.

## Why this direction

The current installed mode works in the first consumer but leaves excessive setup,
update and consumer-owned integration work. The completed rulesync comparison
showed useful SHA acquisition, locking, non-root config merging and skill support
files. Its incremental saving over Git was small under the selected requirements.

The consumer agent reported both alternatives delivered native entries and topics
in real CLI sessions, including folder scope, resume and compaction. Its fixtures
counted 45 added files for rulesync versus 12 for Git/native placement, excluding
engine dependencies and logs. Both still needed safe preparation, independent
identity, configuration ownership, recovery and removal. These are reported trial
results, not independent certification of the proposed tool.

Rulesync's acquisition/generation savings did not justify its additional format,
configuration and dependency surface for these two clients. Reconsider an external
tool only if it removes a substantial portion of construction and ongoing upkeep.

## Acceptance before migration

- Measure complete installation, restoration, update, recovery and removal; no
  per-consumer wrapper/probe and no hidden required configuration stages.
- Verify initial entry, no duplicate injection, topic links, local authority, two
  directory scopes, resume and compaction in both installed clients.
- Test offline prepared use, missing/altered files, path rejection and matching
  implementer/reviewer identity.
- Exercise an update with changed content, interrupted preparation/switching,
  removal after user config edits, and explicit migration from current adapters.
- Complete interactive TUI acceptance and test only available platforms/runtimes;
  a second physical machine and other platforms remain unverified.

The original consumer trial found a guard gap for OpenCode's `apply_patch`; the
consumer subsequently committed a correction with native acceptance evidence.
Verify that correction separately during migration. Copying guard files or passing
smoke tests does not establish coverage of every edit tool.
