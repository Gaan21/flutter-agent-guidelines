# Flutter Agent Guidelines

**Give Claude Code and OpenCode the same Flutter guidance, without loading a whole multi-stack handbook.**

This repository contains the Flutter guidelines and the small tool that loads them into your agent. Your application keeps its own project-specific decisions. There is no second central rule catalog to maintain.

## How it works

After a one-time setup in a Flutter project:

1. **Open your agent normally.** The tool downloads the approved Flutter guidelines and gives the agent a short starting page.
2. **Work with focused context.** The agent reads detailed guidance only when relevant. Project-local rules remain authoritative; subfolder rules keep their original scope.
3. **Review against the same rules.** Other agent sessions in that project join the same saved version, including the reviewer.
4. **Finish the work explicitly.** Once work and review are accepted, the agent or operator marks it finished. After the old sessions exit, the next work uses the latest approved version.

If the guidelines change during work, the tool reports the update but keeps the current version. A new conversation alone does not end the work or change its rules.

The saved copy is called a **snapshot**. It records the exact Git commit and file fingerprints so the tool can detect changed files.

### Shared guidance, local instructions and code checks

```text
Public Flutter guidance       Shared engineering recommendations
AGENTS.md in your project     Project architecture, decisions and commands
lib/data/AGENTS.md            Instructions scoped to that folder
Your analyzer, lints and tests Executable checks on your application
```

The adapter injects the public starting page and its verified identity. Your agent's native instruction loading handles local files; folder instructions keep their original scope. The integration snapshots those local files for identity and drift checks, without turning every folder's instructions into global rules.

For example, when working in `lib/data/`, the agent should apply the project's instructions and the applicable data-folder instructions. An unrelated presentation-folder guide should not become a global requirement. OpenCode and Claude Code loading behavior must be checked separately; a successful test in one client does not verify the other.

Written guidance helps the agent make decisions. Your project's analyzer, lints and tests still check its code separately; the tool does not install a Flutter lint gate.

## What is available today?

- **Development version:** `0.1.0.dev0`, available as source on GitHub and buildable locally. Not published to PyPI, npm, GitHub Packages or pub.dev.
- **Implemented:** local Claude Code/OpenCode integration, automatic snapshots, shared implementation/review identity, update notices and reversible installation.
- **Initial real-project trial:** a reported OpenCode session in a Flutter project received the public guidance and automatically loaded folder-local `AGENTS.md` instructions when reading data and presentation code. This trial used an earlier adapter revision; it does not validate subsequent runtime changes.

| Validation area | Evidence and remaining scope |
|---|---|
| Package and automated behavior | Previously recorded run: 42 automated tests and clean package installation on macOS arm64, Python 3.14.8. This is environment-specific evidence, not a cross-platform guarantee. |
| Client configuration | Earlier probes used Claude Code 2.1.301 and OpenCode 1.19.0. Configuration probes do not prove interactive lifecycle behavior. |
| OpenCode in a real Flutter project | Initial trial reported public injection and folder-local instruction loading. Full lifecycle and subsequent runtime changes still need verification. |
| Claude Code in a real Flutter project | Public injection and folder-local loading still need separate trial verification; an existing `CLAUDE.md` import alone is insufficient evidence. |
| Shared review and shutdown | Same-identity reviewer participation, native session release, restart/resume and crash recovery still need end-to-end trial verification. |
| Recovery and policy changes | Native warning delivery and explicit rebaseline behavior still need trial verification with the updated installed controller. |

**Next:** complete those native lifecycle and recovery checks in controlled consumer trials. Simulated hook events and a successful startup do not prove the whole interactive lifecycle.

## 1. Install the tool once

You need **Python 3.11 or newer**, **Git**, and at least one supported agent. Claude Code must be at least 2.1.295. Python 3.11 is the declared minimum; the test run above used 3.14.8.

Clone this repository into a tools directory, outside your application:

```sh
git clone https://github.com/Gaan21/flutter-agent-guidelines.git
cd flutter-agent-guidelines
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade build setuptools wheel
.venv/bin/python -m build
.venv/bin/python -m pip install --no-deps dist/flutter_agent_guidelines-0.1.0.dev0-py3-none-any.whl
source .venv/bin/activate
flutter-guidelines --help
```

Replace `python3.11` with your available Python >=3.11 executable. These commands use macOS/Linux shell paths; Windows support has not been tested.

Keep the installed environment in place: the project integration records its Python executable. Installing the tool does not add a dependency to your Flutter application's `pubspec.yaml`.

## 2. Connect a Flutter project

Do this once per project, with the project owner's approval. Use an existing project root, not a subfolder:

```sh
PROJECT="/absolute/path/to/your/flutter-project"
flutter-guidelines configure --repo "$PROJECT" \
  --source-url https://github.com/Gaan21/flutter-agent-guidelines.git \
  --source-ref refs/heads/develop
```

This first command shows the proposed configuration. It does not save it. The example chooses this repository's `develop` branch as the approved source of guidelines; you can choose an exact full Git commit instead.

If that source is the one you want, save it:

```sh
flutter-guidelines configure --repo "$PROJECT" \
  --source-url https://github.com/Gaan21/flutter-agent-guidelines.git \
  --source-ref refs/heads/develop --apply
```

The tool discovers existing local `AGENTS.md`, `CLAUDE.md` and Claude rule files. Additional project-specific decisions can be listed with `--policy` or `--overlay`; the scope rules are documented in [Runtime details](docs/runtime.md), section "Context and local scope".

Now preview and apply the agent connection:

```sh
flutter-guidelines install --repo "$PROJECT"
flutter-guidelines install --repo "$PROJECT" --apply
```

By default this connects both agents. Add `--runtime claude` or `--runtime opencode` to both commands if you use only one.

**Quit and restart the selected agents after installation.** From then on, open them normally in the project root. You do not need to activate the Python environment, use a special launcher or supply a task ID each time.

### Check the connection

After restarting, make these checks in each selected client:

1. Ask the agent to identify the injected public source, resolved revision and snapshot identity from its received context. Compare them with the status below; the presence of a plugin file alone does not prove injection.
2. If your project has folder-local instructions, ask the agent to read a source file in that folder before explicitly reading its guide, and report whether the applicable instructions arrived automatically. Repeat for a different folder. Check `AGENTS.md` loading and `CLAUDE.md` imports separately where applicable.
3. Inspect the installed connection and active work from your tools environment:

   ```sh
   flutter-guidelines doctor --repo "$PROJECT"
   flutter-guidelines status --repo "$PROJECT"
   ```

These checks establish initial connection behavior, not the whole work lifecycle. To verify review and closure, use the same work identity in both sessions and observe `end`, session exit and final archival as described in [Runtime details](docs/runtime.md#work-lifecycle). Validate your project's lint/test commands separately, including their failure paths.

### If the project already loads other guidelines

The installer stops when it finds a competing instruction loader. Review that connection before replacing it; do not run two shared rule catalogs together.

Existing protection hooks also need review, rather than deletion. `inventory-hooks` lists Claude hooks; `review-guard` can record approval for an exact non-instruction protection hook. See [Runtime details](docs/runtime.md), section "Installation", before using that approval command.

## 3. Use it day to day

| Situation | What happens |
|---|---|
| First session in a new work unit | Downloads guidelines and records the version automatically. |
| Another session or reviewer joins | Uses the same guidelines and project-policy snapshot. |
| A newer Git commit appears | Reports `UPDATE`; existing work keeps its version. |
| An update check cannot reach the source | Reports `UNKNOWN`; an existing verified snapshot can continue. First preparation needs a successful download. |
| Runtime verification fails | Continues conversation without new guideline injection and shows a warning; protected-state write guards remain active. |
| Project-local policies change | Requires explicit human rebaseline before closure/acceptance; reads and ordinary edits continue. |

To inspect the current work or check for updates, use the installed CLI from an activated tools environment, or its full path:

```sh
flutter-guidelines status --repo "$PROJECT"
flutter-guidelines refresh-check --repo "$PROJECT"
```

**When both implementation and review are finished and accepted**, ask the agent to run:

```sh
flutter-guidelines end --repo "$PROJECT"
```

This marks the work as closing. Existing sessions can finish, new sessions cannot join, and the work is archived after the last session releases its connection. Then start a new conversation for the next work unit.

Closing a window or leaving an agent idle does not count as accepting the work. If a client crashes and leaves a connection recorded, inspect it before using the recovery command `release`. The [runtime contract](docs/runtime.md), section "Work lifecycle", explains this boundary and the native behavior still requiring trial verification.

Updating the installed tool is separate from receiving new guideline content. Close active work and uninstall the old integration before changing its installed controller.

### Source updates and package releases

This repository is already a Python package: `flutter-agent-guidelines` installs the `flutter-guidelines` command. The installation above builds a local wheel; there is no registry release to install yet. It is tooling for your agent, not a Dart or Flutter application dependency.

A Git push makes source changes available. Projects following an approved moving ref can discover new guideline content, while active work keeps its snapshot. Changes to Python or adapter code require rebuilding and reinstalling the tool and its project integration; fetching new guidance does not upgrade the controller. Publishing a versioned package to a registry is a separate release action.

## Remove the project connection

Preview first, then restore the files owned by the installation:

```sh
flutter-guidelines uninstall --repo "$PROJECT"
flutter-guidelines uninstall --repo "$PROJECT" --apply
```

Close the work and exit its sessions first. If an owned file has since been edited, uninstall stops and keeps its backup for inspection. Project configuration, saved snapshots and cache remain available; the tool does not delete them automatically.

## For agents and maintainers

- **Project agents:** use the injected guidelines root and work identity. Read only the relevant guidance and local policies. Reviewer sessions must share that identity; `join --expected DIGEST` provides an explicit check. Mark work closing only after acceptance; do not reset state to obtain newer rules.
- **Repository maintainers:** follow [AGENTS.md](AGENTS.md). The [consumer entry](src/flutter_agent_guidelines/payload/AGENTS.md) is the single starting page shipped with the package.
- **Runtime behavior and commands:** [Runtime details](docs/runtime.md) covers configuration, hook review, installation, failure handling and recovery.
- **Python automation:** [Artifact task API](docs/task-api.md) describes the separate stable-release artifact interface. Its release requirement does not prevent explicitly approved Git-source trials.
- **Standalone content:** `inspect` lists installed content; `export PARENT` saves a snapshot into an existing directory; `verify SNAPSHOT --digest SHA256` checks it against a separately retained fingerprint. These operations do not activate an agent connection.

The runtime fetches allowlisted guideline files and notices, not executable code. The installed package supplies the executable logic. File fingerprints detect differences; source approval is still the owner's decision. Read-only files and tool guards discourage accidental writes, not hostile processes running as the same user.

### Run the package checks

From this tools repository, with the build environment installed:

```sh
.venv/bin/python tests/check_distribution.py
```

This builds the source distribution and wheel in a temporary directory, checks packaged resources, installs the wheel cleanly and runs the tests outside the checkout. `tests/native_smoke.py` additionally probes installed agent configuration without making a model call. Real consumer behavior, other operating systems and the minimum Python version require their own checks.

## License

Apache-2.0 for authorized original material. See [LICENSE](LICENSE), [NOTICE](NOTICE), [Third-party notices](THIRD_PARTY_NOTICES.md) and [Provenance](provenance/README.md). Upstream documentation is linked, not copied or relicensed. Flutter/Dart names do not imply official endorsement.
