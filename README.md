# Flutter Agent Guidelines

**Give Claude Code and OpenCode Flutter instructions automatically when you work in a connected project.**

This is the **guidance package**: written advice and the tool that delivers it to
your agent. [dart-architecture-lints](https://github.com/Gaan21/dart-architecture-lints)
is a **separate lint package** that checks code. They have separate installations.
Guidance does not install or activate the linter; the linter does not load guidance.

## Everyday use, in plain language

| What you tell your project agent | What it should do |
|---|---|
| **"Set up the Flutter guidelines for this repository."** | Install the tools package if needed, connect the chosen clients, record the version, and tell you to restart them. Confirm the initial architecture selection if the project has none. |
| **"Update the Flutter guidelines; there are changes."** | Obtain the current approved source candidate, install it, update the project pin, run checks and report the result. Preserve selected rules and product decisions. |
| **"The Flutter guidelines changed; review them."** | Compare and report. Do not install or change the project. |
| **"Disable this architecture rule in this project."** | Change that rule's executable selection and the corresponding local written contract together; keep the other choices. |

These are instructions to a capable coding agent, **not commands parsed by the
package**. Routine update permission is already given by "update": the agent
should complete the operation, not stop after proposing it or request the same
permission at each step. It should ask only if it finds an incompatible policy,
an unapproved source, a required migration or a genuinely new decision. Git
publication and client restart/exit remain separate capabilities/authorizations.

After setup, open your agent normally. It gets a short starting page and reads
details when relevant. The project keeps its own `AGENTS.md` and folder contracts.
Installed mode needs no work leases, `end` or policy `rebaseline`.

## Can I choose individual rules?

**Yes. Architecture is a starting selection, not an all-or-nothing requirement.**
The owner chooses policy; the agent edits the project's configuration:

| Choice | Where it lives |
|---|---|
| Exact guidance version and optional architecture starting profile | `.flutter-guidelines-installed.json`, written by the CLI |
| Individual executable rules, options and severity | Flutter package's `analysis_options.yaml`, with its locked lint dependency |
| Product architecture and any exceptions to the shared guidance | Root/folder `AGENTS.md` and referenced local contracts |

In the linter's `custom_lint.rules` list, `true` enables a rule and `false` disables
it. For example, a deliberately small selection can keep strict names and method
order without requiring a particular entity generator:

```yaml
custom_lint:
  enable_all_lint_rules: false
  rules:
    - method_order: true
    - variable_name_should_contain_class_name: true
    - domain_entities_must_use_freezed: false
```

This example enables **only two custom rules**. For an existing project, edit its
existing entries rather than replacing its whole configuration with this example.
Severity is separate and belongs under `analyzer.errors`.

If shared guidance recommends the generator but this product does not use it,
record that exception and the chosen alternative locally too. **Silencing a lint
does not by itself change the written architecture.** Local contracts make the
choice visible to the agent; the repository name does not identify a rule set.

The full architecture sample selects 48 of 51 rules; style selects four and legacy
selects all 51. Without explicit selection, the lint plugin retains all 51 defaults.
These are reusable lint samples, not automatic consumer configuration updates.
Only `architecture` is currently a guidance CLI profile name.

The optional recorded lint pair is an advanced check for the stock architecture
selection. It is **not required to use guidance or customize lint rules**, and it
does not certify custom selections or the effective consumer runtime. If a project
already records a pair, change it deliberately rather than attaching an unchanged
stock contract to custom rules. See [project choices](docs/project-workflow.md).

## Does installation get the latest `develop`?

**It depends on what is installed.** A wheel installs the version/bytes in that
wheel. Building a local checkout uses that checkout, even if it is old. Neither
connecting a project nor `upgrade-installed` fetches Git or installs a package.

For this development-source distribution, **"install/update the latest" means the
agent fetches the approved public source's `develop` once, records the exact full
commit and installs that candidate**. An explicit requested commit/release or a
different approved project update policy takes precedence. Later pushes do not
change that installed version. Another request to update repeats this process.

There is no registry release yet; installing a fresh tools checkout from the
approved branch is a source trial, not a PyPI release. The agent can handle these
steps for you; the manual commands below explain what it does.

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

For **"update the Flutter guidelines"**, the agent performs the
[routine update workflow](docs/project-workflow.md#agent-request-update-the-flutter-guidelines):
resolve the approved candidate once, preserve the old environment for rollback,
build/install in a new tools environment, and use that new executable to preview
and apply the project pin/connection change:

```sh
/absolute/tools/flutter-guidelines/bin/flutter-guidelines upgrade-installed --repo "$PROJECT"
/absolute/tools/flutter-guidelines/bin/flutter-guidelines upgrade-installed --repo "$PROJECT" --apply
```

The agent checks compatibility before applying, completes the authorized routine
steps, and reports old/new identities, checks and restart needs. It leaves Git
changes for the normal authorized review/commit workflow. This CLI step itself
does not fetch/install the candidate; the preceding install does that. Restart
affected clients and reload contexts before the next work/review cycle. Old
exports remain intact. See [Installed mode](docs/installed-mode.md).

For **"review the changed guidelines"**, use the
[review-only checklist](docs/project-workflow.md#agent-update-review) instead.

An update does not require changing the linter if its existing contract remains
compatible. If executable rules/options change, separately update the locked lint
dependency and local configuration, run the approved project checks, and refresh
any recorded pair before accepting the new combination. No CLI here installs Dart
dependencies or copies a lint profile into your project.

Do not update the lint dependency just because the guidance changed. If keeping it
would make the requested update incompatible, explain the specific dependency
change needed. A routine guidance update does not authorize changing architecture
choices or refactoring the product to fit new recommendations.

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

### Next delivery model: agent-guides

The completed comparison favors Git acquisition and native Claude Code/OpenCode
loading over rulesync. The owner selected `agent-guides`, a separate neutral Python
package in its own public repository, with PyPI/releases and macOS/Linux support
targets. The goal is one
installation/update operation, a short initial entry and local details read when
relevant. Start with the [agent handoff and tasks](docs/tasks/README.md); the
[agreed scope](docs/delivery-scope.md) records decisions and acceptance boundaries.
This replacement is not implemented; the
installation commands above describe the current package.

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
