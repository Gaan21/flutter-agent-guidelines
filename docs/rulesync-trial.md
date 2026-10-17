# Rulesync product trial

Status: preparation only; no consumer migration. Use the
[product-agent prompt](rulesync-trial-prompt.md) for the real-client trial.
First-consumer outcome and verification handoff: [trial result](rulesync-trial-result.md).
The [review brief](simplification-review.md#next-direction-evaluate-rulesync-first--2026-10-16)
records the goals and owner choices.

## What is ready

- `tools/export_rulesync_trial.py` exports the canonical committed Flutter
  content, notices and a rulesync input into a new disposable directory.
- `rulesync.jsonc` selects only `rules` for `claudecode` and `opencode`;
  no hooks, permissions, MCP servers, skills or global settings are generated.
- `trial-manifest.json` records source revision, selection and SHA-256 inventory.
  Retain its printed digest independently for the trial report.
- No second Markdown source is maintained. The raw payload is copied byte for
  byte from Git blobs. The generated entry adds a trial explanation and changes
  relative topic links to their workspace locations; it is not byte-identical
  to the raw entry. Topic files remain under `.guidelines-trial/payload/` and
  are read when relevant, rather than all being generated as always-on rules.

This is a local evaluation bundle, not a published rulesync source package.
It does not implement source discovery, a one-command consumer install, automatic
technology detection, task approval or runtime integrity checks. Other technology
modules are not supplied. Measure those gaps rather than claiming adoption ready.

## Where to install the tool

Run rulesync where the product's agent prepares the trial. If both repositories
are on the same machine, use the local guidance checkout; no publishing is needed.
Install the exact npm version into a disposable tool directory, not globally or
as a product dependency. Keep it for the duration of the trial and remove it after.

Requirements for this recipe: Git, Python >=3.11 for the export helper, and
Node >=22 with npm for rulesync 36.0.2. Only the runtimes below were tested.
Python is an evaluation-helper requirement, not a rulesync runtime requirement.
Standalone rulesync binaries are another documented option, untested here.

Use the exact published commit supplied with the handoff. An existing local
checkout is sufficient if it contains that commit; otherwise obtain a disposable
checkout from the public repository. Do not reset a dirty shared checkout or
silently substitute an older copy. Pin the commit once for the whole trial.

## Preparation recipe

The product agent chooses paths and records them in local evidence. In these
examples, `GUIDANCE` is the local guidance checkout, `TRIAL` an existing temporary
parent directory, and `SOURCE` a full owner-approved guidance commit. Replace
these placeholders; do not run them literally. `workspace` must not exist yet.
Do not point the exporter at the product repository.

Export from any directory:

```sh
python3 -B "$GUIDANCE/tools/export_rulesync_trial.py" \
  --ref "$SOURCE" --output "$TRIAL/workspace"
```

Use `--architecture` only if the product already selects that profile or the
owner explicitly chooses it. Default is generic; an available profile is not
automatically active. Match the existing product selection before comparison.

Install from the temporary parent, using its own npm cache. No lifecycle scripts
are needed for the generation path tested here:

```sh
npm install --prefix "$TRIAL/tool" --cache "$TRIAL/npm-cache" \
  --ignore-scripts --no-audit --no-fund \
  --registry https://registry.npmjs.org rulesync@36.0.2
```

Record and retain the resulting npm lockfile with local evidence. Use a clean
process environment/home for isolated generation; do not inspect credentials or
copy a developer's home directory. Any later model sessions use the product's
ordinary authorized access, outside the offline command-sandbox experiment.

From **`$TRIAL/workspace`**, run:

```sh
"$TRIAL/tool/node_modules/.bin/rulesync" generate
"$TRIAL/tool/node_modules/.bin/rulesync" generate --check
```

This writes `CLAUDE.md` and `AGENTS.md` in the disposable workspace. Inspect them
before any product integration. Do not run generation directly over existing
product instruction files: rulesync can replace them, even with `delete: false`.
Do not use `--global`, `--delete`, wildcard features or `rulesync init` in the
product. A reversible product trial must preserve existing instruction bytes
and temporarily connect the generated fragment without duplicate old delivery.
Count this manual integration in the result; it is not a finished one-step setup.

## Acceptance and evidence

Record source/engine revisions, profile, npm lock, manifest digest, generated
file hashes and each temporary product change. Preserve unrelated dirty files.
Distinguish verified source bytes, rewritten entry and actual client delivery.
Do not include private product details or local paths in this public repository.

Test actual installed Claude Code and OpenCode sessions, existing local authority,
two directory scopes, coexistence, and absence of duplicate guidance. Add only
clearly labelled disposable diagnostics when needed. Model recall alone does not
prove the full context. Record resume/compaction separately if runnable.

Check generation repeatability and detection of altered generated outputs.
`generate --check` checks generated outputs, not the entire payload inventory or
the model's context. A changed lazy-loaded topic may remain undetected by it.
Check that topic against the independently retained source/inventory instead.

For offline evidence, prepare the tool and workspace first, then run with network
access actually denied where available. An npm offline flag or unreachable proxy
alone is not a process network sandbox. Report unavailable isolation as pending.
No inference-offline claim follows from guidance availability.

Updates must select a new approved source and export a separate workspace.
Never rewrite the active trial while implementer/reviewer are using it. Compare
versions without fabricating a stable release or weakening existing task approval.

Finish with an adopt / small supplement / reject recommendation. Restore the
previous product integration, remove only owned trial files, and retain the report
through the product's authorized workflow. No staging or commits are implicit.

## Preparation checks performed

On macOS, with Python 3.15.0, Node 24.22.0 and npm 11.19.1:

- Three focused unittest cases passed: exact committed source copies and relocated
  entry links, deterministic export/profile selection, and refusal to overwrite
  an existing directory or write into the guidance checkout.
- rulesync 36.0.2 was installed in a disposable directory with lifecycle scripts
  disabled. It generated the two root files; `generate --check` passed.
- Both generated root files contained the same rendered entry. This demonstrates
  generation, not installed-client loading, offline isolation or factory identity.
- Wheel/sdist resource checks and clean installation passed with Python 3.14.8:
  97 package tests passed. The three checkout-only exporter tests were skipped
  there and passed separately in the Git checkout with Python 3.15.0. The export
  helper is source-checkout tooling, not a new installed package command.

No global installation, consumer activation, model session or registry publication
was performed. The disposable installation is removed after preparation checks.

## References

- [rulesync 36.0.2](https://github.com/dyoshikawa/rulesync/tree/v36.0.2)
- [Input roots](https://github.com/dyoshikawa/rulesync/blob/v36.0.2/docs/guide/separate-input-root.md)
- [Configuration](https://github.com/dyoshikawa/rulesync/blob/v36.0.2/docs/guide/configuration.md)
- [File formats](https://github.com/dyoshikawa/rulesync/blob/v36.0.2/docs/reference/file-formats.md)
