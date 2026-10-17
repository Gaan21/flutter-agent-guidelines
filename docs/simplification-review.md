# Simplification review brief

Status: evaluate rulesync before building more delivery tooling (2026-10-16).
Installed mode works in the first consumer but remains too heavy; see
[installed-mode adoption feedback](#installed-mode-adoption-feedback--2026-10-16). Original
review requested by the owner on 2026-10-15. Audience: the next agent or
maintainer asked to review this repository's delivery model. Deliverable: a written
comparison and recommendation. Do not change code, release or consumer
installations as part of the review; the owner decides afterwards.

## Next direction: evaluate rulesync first — 2026-10-16

The owner selected evaluation of [rulesync](https://github.com/dyoshikawa/rulesync)
before further custom installer development. This is an evaluation decision, not
adoption, consumer migration or a verified compatibility claim. A custom common
delivery tool remains a fallback if existing tools cannot meet the requirements.
Use the [trial preparation](rulesync-trial.md) and saved
[product-agent prompt](rulesync-trial-prompt.md) for the next step.
The first-consumer trial is done: see the [trial result](rulesync-trial-result.md)
and its maintainer verification handoff before choosing a custom tool.

### Intended experience

- New repository: one command and at most one restart of each selected client.
- Update: one explicit, obvious operation selecting an exact new version;
  upstream publication and client startup must not silently change the selection.
- Claude Code and OpenCode must receive the selected guidance. No consumer-owned
  installer or integration probe should be necessary for routine use.
- Maintain original Markdown guidance as technology modules, reusable across
  repositories. Examples include Flutter, Supabase, C#, Astro and TypeScript;
  these are desired combinations, not a claim that modules already exist.
- A repository selects its modules explicitly; mixed repositories need scoped
  selections by directory. Available content need not become loaded context.
- Keep a short starting entry and consult detailed guidance when relevant.
  Preserve local project authority, folder scope, existing hooks and guards.
- Keep guidance independent from executable lints and their dependency versions.
  Selecting Flutter guidance must not install or update dart-architecture-lints.

### What an existing tool might replace

Rulesync documents shared sources, content selection, client-specific generation
and revision/hash locks. These are candidates to replace our acquisition and
generation machinery, not evidence that all runtime guarantees are equivalent.
Markdown may need tool-specific metadata and project configuration. A generator
does not establish client loading, behavioral compliance or task identity merely
by producing files. See its [declarative source documentation](https://github.com/dyoshikawa/rulesync/blob/main/docs/guide/declarative-sources.md).

Do not choose Python, uv, PyPI or a custom hook architecture before evaluating the
existing tool. Package runners and standalone binaries are distribution options;
their prerequisites and first-use downloads must be counted in the trial.

### Automated consumer requirements

A trusted host prepares the repository before agents start. Agent commands run
without network access or credentials; preparation must require no interactive
restart. Pin the engine, source revision, selected bundles, local policy and
overlays once for both implementer and reviewer. Verify the delivered guidance
against that independently retained identity; never resolve latest per role or
modify a live snapshot. Distinguish source bytes from any client transformation.
Hashes establish integrity, not publisher trust or proof of client delivery.

### Trial and acceptance

Local generation experiments use disposable fixtures outside this repository
and consumers. The owner also selected a real product-repository trial, carried
out by that repository's agent under its own instructions and authorization.
Record an exact released rulesync version and source revision, prerequisites,
commands, generated files and hashes. Preserve the canonical payload; do not
import third-party rule collections. Remove disposable trial files afterwards.

Measure content selection, repeatability, update behavior, prepared offline use,
tamper/missing-file handling and coexistence with local instructions. Count actual
setup/update steps. A frozen dependency lock must not be assumed to disable
network access. Record separately what is documented, statically checked and
tested in installed clients.

Client acceptance must cover first-turn delivery, directory scope, resume and
compaction in both clients. Scope, model execution and credentials for such trials
need explicit authorization; generated files alone cannot establish this result.
If rulesync leaves gaps, assess whether a small trusted-host check can fill them
before choosing another tool or building a replacement.

### Owner-confirmed choices

- Suggest technologies and directory scopes initially, then obtain confirmation
  and persist the selection. Do not silently activate modules on later starts.
- Start with one shared content release; each repository activates only its
  selected modules. Independent per-module versions remain a possible extension.
- Explicit local product decisions override common guidance. Preserve and report
  exceptions without silently rewriting product architecture or lint selections.
- Evaluate in a real product repository through its own agent, including actual
  Claude Code and OpenCode sessions. Generation-only checks are insufficient.
  This document does not itself activate a consumer or authorize global changes.

The product trial must inventory existing loaders, protect unrelated settings
and guards, and define a reversible test arrangement without double injection.
Keep installation/generation evidence separate from observed client delivery.
Where a client session cannot be run or inspected, report that check as pending;
do not substitute a model's claimed compliance for delivery evidence. Record any
limitations in demonstrating exact source text, folder scope or task identity.

## Owner-selected direction — 2026-10-16

The owner chose explicit installed-version selection instead of the current
cross-session work lifecycle. Package distribution remains suitable: agents use
the selected installed guidance until an explicit update changes it. Opening a
conversation or pushing upstream must not select a newer revision automatically.

- Prefer a project-recorded exact version/revision and content fingerprint so
  implementation and review can check the same identity across machines.
- A machine-level installation may supply that version, but installation alone
  does not establish a shared project pin. Version mismatches must be visible.
- Plan updates between work/review cycles and reload affected agent contexts;
  existing conversations retain instructions already delivered.
- Evaluate removing work leases, mandatory `end`, and policy `rebaseline` from
  the replacement delivery model. Keep focused reading and native local scope.
- The owner subsequently authorized implementation. See [installed mode](installed-mode.md)
  and [project choices/update review](project-workflow.md) for the candidate and
  explicit migration. Legacy consumers retain their current behavior until
  migration; consumer activation/native validation remain separate steps.

## Installed-mode adoption feedback — 2026-10-16

The first consumer migrated to installed mode (`6687627`) and verified it in a
fresh session: injected identity equals `status`/`doctor`, both clients connected,
project guards intact. It works, but the owner's verdict is that installation and
updating are **still too complex**: it should be one command and done. Installed
mode removed leases, `end` and `rebaseline`; it did not remove the setup and update
mechanics around them.

What the consumer still has to run or maintain:

- **Prerequisites:** Git, uv, Python 3.14, one immutable virtual environment per
  approved commit, provenance check of the installed distribution.
- **First connection:** approval JSON, then `configure --installed` preview/apply,
  `install` preview/apply, `doctor --expected <identity>`, restart both clients.
- **Each update:** fetch the ref, edit `installed_commit`, provision a new
  environment, `upgrade-installed` preview/apply, `doctor`, consumer probe and hook
  smoke tests, restart both clients, commit the new pin.
- **Consumer-owned glue:** an 80-line staged installer wrapper, an 85-line
  integration probe and roughly 270 lines of setup, update and evidence docs.
- **Migration cost:** legacy rebaseline, `end`, uninstall, archiving legacy
  configuration, three installer stages, restarts and a separate verification
  session; some edits had to wait until the legacy guard was gone.

Defects and rough edges seen during the migration:

- Legacy `uninstall` removed the ignore entry for legacy state that it leaves on
  disk, so the retained state appeared untracked and could be committed.
- Importing the generated OpenCode plugin outside OpenCode (consumer probe) prints
  a Node module-type warning.

Directions the owner asked to evaluate (no decision yet):

1. **One command.** A single `install`/`update` entry point in the package (for
   example `uvx`/`pipx run … sync --repo .`) that reads the project approval,
   provisions the environment, writes the pin, connects both clients and runs
   `doctor`, so consumers need no wrapper script. Preview stays available as an
   option rather than a mandatory stage.
2. **Split packages.** Separate guidance content (Markdown, versioned per stack)
   from a small stack-agnostic delivery tool, so content updates do not imply new
   executable code and a second stack reuses the same tool.
3. **Publish releases.** Tagged releases on a registry (PyPI) or client-native
   marketplaces (Claude Code plugins, OpenCode equivalent) so updating is "bump a
   version" instead of commit SHAs and per-commit environments.
4. **Revisit the alternatives below** (plain Git content, native packaging, thin
   fetch hook) against the success criteria, now with installed-mode evidence.

Measure any proposal against the success criteria: one command plus at most one
restart for a new repository, and a single obvious step for updates.

## Why

The first real consumer adoption (a private Flutter app, Claude Code and OpenCode)
works, but setting it up and keeping it running took several sessions of owner and
agent time. The owner wants future guidance for **other frameworks and stacks**
(for example a web framework or a backend platform, in other repositories) to be
much simpler to install and use. Before extracting another stack, find out whether
a simpler mechanism gives the same practical result.

Scale today: about 2,200 lines of Python and adapter code plus 1,300 lines of tests
and 700 lines of documentation deliver 5 Markdown guidance files. The consumer
additionally keeps a staged installer wrapper, an integration probe and a
setup/evidence document of several hundred lines.

## What must keep working

Treat each item as a hypothesis to confirm with the owner, not a fixed contract.
Mark which ones a simpler design keeps, weakens or drops.

1. **Focused context.** Agents get a short common entry page and read detailed
   guidance only when relevant, instead of a whole handbook.
2. **Local authority and scope.** Project `AGENTS.md`/`CLAUDE.md` and folder-level
   guides stay authoritative; folder rules apply only in their folder.
3. **Hands-off updates.** Approved changes in the guidance source reach consumers
   without editing commit SHAs repository by repository.
4. **Stable version during a unit of work.** Implementer and reviewer use the same
   guidance revision; updates do not change rules mid-task.
5. **Traceability.** It is possible to say exactly which revision a piece of work
   used.
6. **Both clients.** Claude Code and OpenCode receive the same guidance.
7. **Coexistence.** Existing project hooks and guards keep working.
8. **Multiple stacks.** Adding a new framework means adding content, not a new
   tool, installer or lifecycle.

## Current process end to end

As of runtime bootstrap `6d328c3` and content `e8ac7ca`, as actually run by the
first consumer (macOS arm64, zsh, Claude Code and OpenCode). Commands use
`cli` for `<tools-venv>/bin/python -I -m flutter_agent_guidelines.cli`.

### One-time setup per machine and repository

1. **Tools environment.** Create a dedicated virtual environment and install the
   package from Git at the bootstrap commit. The consumer uses one immutable
   environment per bootstrap commit (`uv venv --python 3.14` plus
   `uv pip install "flutter-agent-guidelines @ git+<url>@<bootstrap>"`) and checks
   the installed distribution's origin and commit. Installed hooks record this
   Python executable, so the environment is never upgraded in place.
2. **Approval record (consumer convention).** A versioned JSON file in the
   consumer: source URL, ref (`refs/heads/develop`), `auto_update: true`,
   bootstrap commit.
3. **Configure.** `cli configure --repo P --source-url U --source-ref R
   --auto-update` previews; `--apply` writes the ignored machine-local runtime
   configuration at the consumer root. Refuses while a work is active or a
   previous integration is installed.
4. **Review existing guards.** `cli inventory-hooks --repo P` lists project hooks
   with fingerprints; each existing PreToolUse guard must be attested with
   `cli review-guard --repo P --source S --digest D --non-instruction-guard
   --apply`. Unreviewed guards are not accepted.
5. **Install.** `cli install --repo P` previews; `--apply` writes the Claude Code
   hooks into the ignored local Claude settings and generates the OpenCode
   adapter plugin; then `cli doctor --repo P`.
6. **Restart both clients** and verify in each one: injected source, revision and
   snapshot identity; folder-guide loading; `doctor` and `status`.

The consumer wrapped steps 1, 3, 4 and 5 in a staged installer script (no
argument, `--configure`, `--install`) and added an integration probe.

### Each unit of work

- **Start.** The first session's start/prompt hook runs the bootstrap: it resolves
  the ref to a commit, prepares that controller, adapters and guidance,
  snapshots the local policy files, creates a work identity, records a session
  lease and injects the entry page.
- **Join.** Further conversations, including the reviewer, join the same work.
- **Upstream push.** Only reported as `UPDATE`; nothing changes for open work.
- **Local policy edit** (any discovered `AGENTS.md`/`CLAUDE.md`). Work moves to
  `rebaseline-required`; reads and edits continue; `end` is refused until
  `cli rebaseline --repo P` (plan) and `--apply`, which require zero registered
  sessions, so they run from a terminal after exiting every client.
- **Finish.** After acceptance, `cli end --repo P` marks the work closing; it is
  archived when the last session releases its lease on exit. The next
  conversation starts a new work at the latest revision. Without `end`, the
  consumer stays on the old revision indefinitely.

### Changes and recovery actually needed

- **Bootstrap migration** (manual controller to automatic updates): `end`, exit
  all sessions, `uninstall` with the old CLI, create the new tools environment,
  configure, review guards, install, restart, verify. It took several sessions.
- **Removing one project guard hook.** Every command then failed with
  `reviewed guard missing/changed`; there is no CLI command to drop a review.
  Removing the entry from the machine-local configuration by hand then failed
  every command with `configuration drift during pinned work`, including the
  session release on exit, while `rebaseline` refuses with registered sessions.
  Working order: restore the guard entry and the configuration so state is
  consistent, exit the sessions, then remove the guard and its review entry,
  run `rebaseline --apply` (it accepts the new configuration) and `doctor`.
- **Agent limits.** The runtime's protection guard blocks agent writes and
  searches touching protected state. It also matches file *content*: writing a
  recovery script, and even editing this document in another repository, was
  rejected because the text named the runtime's own files. Most lifecycle and
  recovery steps were therefore handed to the owner as terminal commands. A
  multi-line shell function pasted into a terminal broke on a line wrap and left
  an interactive Python prompt waiting.

## Friction observed in the first adoption

- **Install prerequisites:** uv, a dedicated Python 3.14 virtual environment per
  bootstrap commit, staged `configure`/`install` each with preview then `--apply`,
  then restarting both clients. The consumer wrote its own wrapper script to make
  this repeatable.
- **Many concepts:** channel, bootstrap, controller, deployment, snapshot, work,
  lease, session, digest, reviewed guard, rebaseline. Owners and agents needed
  explanations before every lifecycle step.
- **Explicit lifecycle:** a new version only arrives after `end` plus exit of every
  session. If nobody runs `end`, the repository stays on the old version
  indefinitely. Editing any local `AGENTS.md` requires a human `rebaseline` before
  `end`.
- **Agent cannot finish the loop:** lifecycle commands refuse while the agent's own
  session holds a lease, so each migration, rebaseline and closure was handed back
  to the owner as a terminal script.
- **Fragile coupling to local hooks:** removing one unrelated project PreToolUse
  hook invalidated its recorded review fingerprint; afterwards `status`, `doctor`
  and `rebaseline` all failed until the owner hand-edited the machine-local
  configuration. A one-line settings change cascaded into a recovery procedure.
- **Protected state blocks normal work:** the write/execute guard also rejected an
  ordinary repository-wide search and an agent writing a recovery script that only
  mentioned the protected configuration path.
- **Bootstrap migration:** moving from the manual controller to automatic updates
  required closing work, uninstalling, a new tools environment, reinstalling,
  restarting and re-verifying, across several sessions.
- **Executable auto-update:** following a branch approves running new Python and
  adapter code, not just reading Markdown. This raises the trust bar for every push.
- **Stack naming:** the package, commands and state paths are Flutter-named; a
  second stack would duplicate the whole runtime as currently shaped.
- **Documentation traps:** shell snippets stored commands in variables, which fails
  in zsh.

## Alternatives to evaluate

Check current official documentation for each client before concluding; client
capabilities change quickly. Evaluate each against the list above and the cost of
installing it in a new repository.

1. **Plain Git content.** Guidance repository as a submodule, subtree or sibling
   checkout; project `AGENTS.md`/`CLAUDE.md` import or reference the entry page.
   Updates are a reviewed submodule bump or pull; the commit pins the revision for
   implementer and reviewer.
2. **Client-native packaging.** Distribute guidance as Claude Code plugin(s) and
   skills (on-demand loading gives focused context) and the OpenCode equivalent
   (skills, `instructions` entries, plugins). One package per stack; updates through
   the client's own marketplace or update mechanism.
3. **Remote instructions with a pin.** Clients that accept URL or glob instruction
   sources read a tagged revision directly; the project records the tag.
4. **Thin fetch hook.** A single small session-start hook fetches a pinned or
   channel revision into an ignored cache and injects the entry page. No leases,
   no guard reviews, no executable updates.
5. **Reduced current runtime.** Keep the Python tool but drop the parts with the
   worst cost/benefit (for example executable updates, guard fingerprints, leases
   or mandatory `end`), and make it stack-agnostic with per-stack content.

Combinations are acceptable, for example plain Git or native packaging for
content plus an optional check that records the revision used.

## Questions to answer

- Which requirements above does each alternative meet in practice, and which ones
  does the owner actually need? Is per-work version locking worth its lifecycle
  cost, or is "the revision at the time of the commit" enough traceability?
- What is the minimum consumer footprint: number of commands, files committed in
  the consumer, prerequisites, client restarts?
- How does an update reach a consumer, and who has to act?
- What breaks when a consumer edits its own `AGENTS.md`, hooks or settings?
- How would a second stack be added, and can one repository consume two stacks?
- What is the migration path for the existing consumer, and can it be done in one
  session?

## Success criteria for a recommendation

- New repository: one documented command (or a short copy-paste block) plus at
  most one client restart, no consumer-maintained scripts.
- Updates: no human lifecycle step, or a single obvious one.
- Local edits to project rules or hooks never break the guidance tooling.
- An agent can explain the whole setup to the owner in under ten lines.
- Adding a new stack is mostly writing guidance content.

## Inputs

- This repository: `README.md`, `docs/runtime.md`, `docs/automatic-updates.md`,
  `src/flutter_agent_guidelines/payload/AGENTS.md`.
- Consumer evidence (setup document, installer wrapper, integration probe, session
  history) is in a private repository; ask the owner for access or excerpts.
