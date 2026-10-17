# Rulesync product trial: result and verification handoff

Status: first-consumer trial completed 2026-10-16; recommendation pending
maintainer verification. Inputs: [trial recipe](rulesync-trial.md) and
[product-agent prompt](rulesync-trial-prompt.md) at `c9ede89`. Private paths,
product details and logs stay in the consumer's evidence location.

## What was tested

- Source `c9ede89f0074808a9bbe4ba19a6a740ec92b5231`, `--architecture` profile
  (the consumer's existing selection). The exported payload was byte-identical
  to the consumer's installed payload; only the entry preamble and links differ.
- rulesync 36.0.2 in a disposable directory, private npm cache, lifecycle scripts
  disabled, clean `HOME`. Lock: 272 packages, SHA-256
  `9559ea3709f37d3bbbb4f54ffd4c6487777645a2b0f50279ccdb6a86d95b9d07`.
- Manifest `00fa4315907eda9e61ac079371962012517b657c184aa99294599ce162e1a789`;
  rule source `88493fe7…`; rendered entry `b0ed6172…` (both root files equal).
- macOS, Node 24.22.0, npm 11.19.1, Python 3.15.0; Claude Code 2.1.302 headless
  (`-p`); OpenCode 1.19.3 (`run`, an OpenAI model).

Because the consumer agent could not change its own client configuration in place
(the agent self-modification policy refused it), the client checks ran in a
disposable clone of the consumer at its current revision. The clone carried the
tracked instructions, hooks and guard plugins but no ignored installed adapter,
so there was no double delivery. The live checkout stayed unchanged.

Integration was manual. The rendered entry went to `.claude/rules/` (Claude) and to
a file listed in OpenCode `instructions` from a new `.opencode/opencode.jsonc`.
The payload was copied to `.guidelines-trial/`. rulesync was not run in the
consumer, for two reasons:

- Root mode writes `CLAUDE.md` and `AGENTS.md`, which would replace the
  consumer's own files.
- Non-root mode writes `.claude/rules/<name>.md`, `.opencode/memories/<name>.md`
  and a root `opencode.jsonc` with `instructions`. Its behavior against an
  existing consumer `opencode.jsonc` was not tested.

## Observed results

| Check | Claude Code | OpenCode |
| --- | --- | --- |
| First-turn delivery | pass (`/context` memory files) | pass (system-prompt diagnostic plugin) |
| One copy, no installed block | pass | pass, every turn |
| Topic link from entry | pass, root-relative | pass |
| Local root authority kept | pass | pass |
| Two folder scopes | pass (`nested_memory`) | pass (attached to `read` output) |
| Resume | pass | pass |
| Compaction | pass for entry; folder scopes until re-read | pass (server summarize); same |
| Existing guard coexistence | pass | see below |
| Interactive TUI | pending | pending |

The folder-scope behavior after compaction is native client behavior, unrelated to
rulesync.

The consumer's OpenCode guard plugin inspected only `write` and `edit`. With OpenAI
models OpenCode edits through `apply_patch`, so the guarded change went through.
This consumer defect is independent of rulesync. Any future delivery that ships
tool guards must cover every edit tool.

Generation checks:

- Repeated and independent export plus generation was byte-identical.
- `generate --check` detects modified or missing generated root files and an
  edited rule source. It does **not** detect a modified or deleted lazy topic
  file; only the independent manifest comparison does.
- Under a real network-denied process sandbox (`sandbox-exec`, confirmed by a
  failing request), generation, `--check` and manifest verification passed with
  identical bytes. Offline client inference was not tested.
- A separate export from the approved `6687627b` produced manifest `7dc6b218…`.
  The payload was unchanged; only the entry revision line differed.

## Assessment

- Delivery itself worked in both clients without hooks or a Python runtime.
  Native loaders did that work: Claude `.claude/rules/` and OpenCode
  `instructions`.
- rulesync contributed only rendering. It copied one Markdown file and removed
  its frontmatter.
- Still custom or manual:
  - acquisition through the export helper;
  - payload placement and entry placement for each client;
  - removal of the old adapter;
  - topic integrity checking.
- No one-command install. About 10 steps to install and about 6 to update.
  Prerequisites: Git, Python >= 3.11 and Node >= 22 with npm (network for
  272 packages).

Consumer-agent recommendation: do not adopt rulesync as tested. Prefer native
loader placement plus a small trusted-host manifest check.

## Maintainer verification requested

Owner direction: verify this result. Then build our own minimal delivery tool
only if no existing alternative meets the requirements in the
[review brief](simplification-review.md#next-direction-evaluate-rulesync-first--2026-10-16).

1. Reproduce the generation, tamper and network-denied checks with disposable
   fixtures. They need no consumer.
2. Evaluate untested rulesync capabilities before rejecting it:
   - declarative sources and the lock fetching an exact revision;
   - non-root output against an existing `opencode.jsonc`, merge or replace;
   - whether config emission can be avoided;
   - whether non-rule payload files can be delivered.
3. Briefly compare other existing options: plain Git placement with native
   loaders; OpenCode `instructions`, including commit-pinned remote URLs and
   their startup network cost; client plugin or packaging mechanisms. Record
   documented, tested and untested capabilities separately.
4. If nothing fits, scope the minimal tool from this trial:
   - fetch an exact revision;
   - place the payload and native entries without replacing consumer files;
   - record a manifest;
   - `verify` every placed file, including topics, before sessions start;
   - `remove`.

   The tool must work without client hooks or a client runtime, never resolve
   latest implicitly, and stay separate from executable lints.

Do not change the consumer while verifying. The consumer interactive TUI checks
remain pending for the owner.
