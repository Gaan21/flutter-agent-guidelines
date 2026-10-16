# Simplification review brief

Status: open, requested by the owner on 2026-10-15. Audience: the next agent or
maintainer asked to review this repository's delivery model. Deliverable: a written
comparison and recommendation. Do not change code, release or consumer
installations as part of the review; the owner decides afterwards.

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
