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

## What is available today?

- **Development version:** `0.1.0.dev0`, available as source on GitHub and buildable locally. Not published to PyPI, npm, GitHub Packages or pub.dev.
- **Implemented:** local Claude Code/OpenCode integration, automatic snapshots, shared implementation/review identity, update notices and reversible installation.
- **Verified:** 42 automated tests and clean package installation on macOS arm64 with Python 3.14.8. Earlier configuration probes used Claude Code 2.1.301 and OpenCode 1.19.0; native dispatch of the recovery behavior still requires trial verification.
- **Next:** controlled use in a real Flutter project, including actual session startup, review and shutdown. Configuration probes and simulated hook events do not prove the whole interactive lifecycle.

This tool loads written guidance. Your project's analyzer, lints and tests still check its code separately.

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
