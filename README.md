# Flutter Agent Guidelines

**Give Claude Code and OpenCode the same focused Flutter guidance, using an explicitly selected installed version.**

Install the Python tool once in a tools environment, then connect each project
explicitly. The project records the exact payload and controller identity. Opening
a conversation or pushing upstream never selects a new version or fetches Git.

## How it works

1. Install an owner-approved package in a dedicated tools environment.
2. Record its exact identity in the project's versioned pin and install the local connection.
3. Open your agent normally. It receives the short public entry page; details are read only when relevant.
4. Implementer and reviewer compare the same project identity, including on different machines.
5. Update the package and project pin explicitly between work/review cycles, then reload agent contexts.

There are no work leases, mandatory `end`, or policy `rebaseline` in installed
mode. Editing local `AGENTS.md`, `CLAUDE.md` or ordinary tool guards does not change
the public guidance identity. Native project and folder instructions retain their
authority and scope. Analyzer, lint and test execution remains project-owned.

## What a project chooses

There are three separate inputs; installing one does not activate the others:

| Input | Selected in | Effect |
|---|---|---|
| Guidance version and profile | `.flutter-guidelines-installed.json`, through the CLI | Which written guidance the agent receives and follows |
| Executable lint rules, options and severity | The Flutter package's `analysis_options.yaml`, with its locked lint dependency | Which diagnostics actually run |
| Product decisions and exceptions | Project/folder `AGENTS.md`, native Claude instructions, and referenced local contracts | What applies to this product and these files |

The owner chooses; an agent implements the approved selection. The tool does not
guess a product from its repository name. Two Flutter products can share the same
guidance version and choose different lint selections and local contracts. A
monorepo can give each Flutter package its own lint configuration and scoped guides.

The optional `architecture` guidance profile is a reusable convention, **not a
product identity**. It recommends the matching 48-rule lint selection, including
strict names and member order. Generic guidance selects no such architecture.
The linter also offers a four-rule style sample and a 51-rule legacy sample;
these are lint samples, not additional `--profile` names in this guidance CLI.

For a different rule selection, change the executable configuration and document
the approved deviation in local instructions in the same review. Never just
disable a diagnostic while leaving its obligation unexplained to the agent.
The optional recorded pair checks the **stock 48-enabled architecture selection**
and selective typing. It records other declared options/severities; it does not
validate arbitrary consumer overrides or attest the effective consumer runtime.
See [project selection and updates](docs/project-workflow.md).

## 1. Install the tool once

Requires Python **>=3.11**. Use a dedicated tools environment outside your Flutter
application; this is not a `pubspec.yaml` dependency. There is currently only a
development version (`0.1.0.dev0`), not a published registry release. For an
explicitly owner-approved source trial, build and install a reviewed checkout:

```sh
python3.14 -m venv /absolute/tools/flutter-guidelines
python3.14 -m venv .build-env
.build-env/bin/python -m pip install build setuptools wheel
.build-env/bin/python -m build
/absolute/tools/flutter-guidelines/bin/python -m pip install --no-deps dist/flutter_agent_guidelines-0.1.0.dev0-py3-none-any.whl
```

Run the build commands in the reviewed tools repository. Replace `python3.14`
with your available supported Python. These examples use macOS/Linux paths;
Windows is unverified. Once stable releases exist, install the owner's selected
exact release wheel instead. Hashes establish integrity, **not publisher trust**.
The separate artifact task approval API still requires stable releases.

## 2. Connect a project explicitly

Use the installed executable (or activate its environment). Commands preview by
default; `--apply` authorizes writes to the selected project:

```sh
PROJECT="/absolute/path/to/flutter-project"
/absolute/tools/flutter-guidelines/bin/flutter-guidelines configure --installed --repo "$PROJECT"
/absolute/tools/flutter-guidelines/bin/flutter-guidelines configure --installed --repo "$PROJECT" --apply
/absolute/tools/flutter-guidelines/bin/flutter-guidelines install --repo "$PROJECT"
/absolute/tools/flutter-guidelines/bin/flutter-guidelines install --repo "$PROJECT" --apply
```

The default connects both clients; add `--runtime claude` or `--runtime opencode`
to both `install` commands to select one. Keep the tools environment at its path:
the local connection records its interpreter, without a shell activation requirement.

### Optional strict architecture profile

Generic guidance is the default: no profile is activated automatically. For
projects choosing the stricter architecture contract, add `--profile architecture`
to both `configure --installed` commands above. This is the recommended option
when the project owner selects those strict architecture and code-structure rules.
The selected `profiles/architecture.md` is part of the pinned package; context
names it and requires consulting it before implementation when applicable,
without injecting the whole profile inline.

To pair it with an independently verified linter source/configuration, add
`--lint-contract CONTRACT.json` to configure. The pin embeds the complete exported
contract and canonical digest, without the artifact's machine path. An existing
pair changes only through `upgrade-installed --lint-contract CONTRACT.json` or
`--clear-lint-contract` (preview, then `--apply`); omission preserves it.
Architecture without a pair is allowed and explicitly reports **lint contract:
unrecorded**. A recorded pair is **not installed-runtime verification**. See
[recorded lint pairing](docs/installed-mode.md#optional-recorded-lint-pairing) for
source verification and export steps; guidance never runs Dart or installs a linter.

### Record and check the connection

Commit **`.flutter-guidelines-installed.json`** through your normal review
process. It records package version, payload, complete export, controller and profile
fingerprints, without machine paths. The local immutable export, connection
record and client integration files are ignored. Another machine installs the
same exact package and runs `install` against the checked-in pin. A different
package refuses injection and reports the mismatch; it never rewrites the pin.

Restart selected clients once after connection. In each client, check that the
injected identity matches `status`, and check native folder-guide loading in two
different folders. Presence of a plugin file alone does not prove delivery.

```sh
/absolute/tools/flutter-guidelines/bin/flutter-guidelines status --repo "$PROJECT"
/absolute/tools/flutter-guidelines/bin/flutter-guidelines doctor --repo "$PROJECT" --expected IDENTITY_SHA256
```

`--expected` checks an independently retained project identity, suitable for the
reviewer. Installed-mode `doctor` is offline verification; it does not launch
product commands. Runtime warnings continue the conversation without fresh
guidance injection. Instructions already delivered remain in existing contexts.

## 3. Updates are explicit

**"The Flutter guidelines package changed; review it" means review, not update.**
The agent should identify the current delivery mode, guidance pin, selected profile,
resolved linter and effective local configuration; inspect an identified candidate;
then report changes, affected local contracts and the proposed update/migration.
It must not upgrade packages, rewrite pins, switch profiles or close work merely
because a review was requested. A push is neither a registry release nor an
installed update. [The agent checklist](docs/project-workflow.md#agent-update-review)
defines this workflow, including legacy installations.

Git pushes and conversations do nothing to version selection. Install the new
owner-approved package into the tools environment (or a new tools environment),
then preview and apply the project change using that new executable:

```sh
/absolute/tools/flutter-guidelines/bin/flutter-guidelines upgrade-installed --repo "$PROJECT"
/absolute/tools/flutter-guidelines/bin/flutter-guidelines upgrade-installed --repo "$PROJECT" --apply
```

This shows the old and new exact pins, creates a new immutable export, and
refreshes the owned connection to the selected interpreter. It never installs a
package or updates an executable itself. Review and commit the changed pin;
restart affected clients and reload contexts before the next work/review cycle.
Old exports are retained, never edited. Keep exact wheels available for matching
other machines or rollback. See [Installed mode](docs/installed-mode.md).

An update does not require changing the linter if its existing contract remains
compatible. If executable rules/options change, separately update the locked lint
dependency and local configuration, run the approved project checks, and refresh
any recorded pair before accepting the new combination. No CLI here installs Dart
dependencies or copies a lint profile into your project.

Omitting profile options preserves the current choice during configure or upgrade.
Changing profiles requires explicit `upgrade-installed --profile architecture`
(preview, then `--apply`); use `upgrade-installed --clear-profiles` to return to
generic guidance. Re-running configure cannot silently change an existing choice.

## Coexistence, removal and legacy migration

The installer preserves unrelated settings and ordinary tool guards. It inventories
only the selected clients, so unused-client configuration does not block a
single-client connection. It reports
possible competing entry loaders and OpenCode instruction/plugin configuration
for explicit inventory rather than silently ignoring them. Native local
instruction files remain native; they are not frozen into a global policy list.
No content-matching write/execute guard is installed by this mode.

To remove just the connection, preview and apply `uninstall --repo "$PROJECT"`.
It removes the owned hooks/plugin while preserving unrelated settings, the pin,
exports and ignore entries. Modified owned hooks/plugins require inspection.
No work closure is needed in installed mode.

**Existing installations are legacy and are not migrated automatically.** Their
work/lease behavior is unchanged. With the original installed CLI, finish and
close the work, exit/release sessions, and preview/apply legacy `uninstall`.
Then explicitly archive/remove the old `.flutter-guidelines.json` configuration
before configuring installed mode. Do not edit a live legacy snapshot. See the
[migration procedure](docs/installed-mode.md#legacy-migration).

Legacy source selection and `--auto-update` remain explicit compatibility paths:
[Legacy runtime](docs/runtime.md), [automatic updates](docs/automatic-updates.md).
The [artifact task API](docs/task-api.md) retains its task identity contract.

## Verification and limits

Installed-mode Python subprocess tests and a direct Node adapter harness verify
offline delivery, portable identity, mismatch/tamper/path rejection, explicit
upgrade, guard coexistence and removal. The new mode still needs installed-client
interactive trials in Claude Code and OpenCode: entry delivery, warning display,
resume/compaction and native folder scope are not established by configuration or
simulated hook tests. There are no release-event or shutdown semantics to verify
for this mode. Test only Python versions and platforms actually available.

```sh
.build-env/bin/python tests/check_distribution.py
```

This builds wheel/sdist, verifies exact resources and notices, installs cleanly,
and runs tests outside the checkout. `inspect`, `export PARENT`, and `verify
SNAPSHOT --digest SHA256` remain standalone content operations. They do not
activate a consumer. Read-only files discourage accidental edits, not hostile
same-user processes.

Maintainers follow [AGENTS.md](AGENTS.md). The canonical consumer entry is
[payload/AGENTS.md](src/flutter_agent_guidelines/payload/AGENTS.md).

## License

Apache-2.0 for authorized original material. See [LICENSE](LICENSE), [NOTICE](NOTICE),
[Third-party notices](THIRD_PARTY_NOTICES.md) and [Provenance](provenance/README.md).
Third-party guidance is linked, not copied or relicensed. Flutter/Dart names do
not imply official endorsement.
