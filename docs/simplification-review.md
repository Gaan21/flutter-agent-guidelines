# Simplification review brief

Status: installed-version direction selected; implementation candidate prepared
and package-tested, with consumer migration/native trials still pending. Original
review requested by the owner on 2026-10-15. Audience: the next agent or
maintainer asked to review this repository's delivery model. Deliverable: a written
comparison and recommendation. Do not change code, release or consumer
installations as part of the review; the owner decides afterwards.

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
