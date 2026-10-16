# Installed-version delivery

This is the recommended project connection. Legacy source-following and artifact
task interfaces remain available separately. No consumer is migrated implicitly.

## Identity and storage

`configure --installed --repo PROJECT` previews the exact currently installed
package. `--apply` records `.flutter-guidelines-installed.json` and creates a
content-addressed, read-only export under `.flutter-guidelines-installed/`.
The pin is intended for version control; the export is machine-local and ignored.
There is one canonical packaged payload; exports are verified copies of it.

The portable pin includes schema/mode, package name and version, payload digest,
complete bundle manifest digest (including notices), controller digest, and selected
`profiles` list. The
controller digest covers installed Python modules and adapter JavaScript, not
absolute interpreter paths, bytecode or local instructions. The project identity
is SHA-256 of the canonical pin JSON. Same labels with different bytes do not
match. Keep exact approved wheels for reproducibility; version labels alone are
insufficient, especially for development builds.

### Optional architecture selection

By default `profiles: []` selects generic guidance. Projects choosing the strict
architecture contract should opt in with `configure --installed --profile
architecture --repo PROJECT` (preview, then `--apply`). The only supported profile
name is `architecture`, mapping to `profiles/architecture.md` under the guidance
root. Unknown, malformed or duplicate names are rejected. The complete installed
package fingerprint includes the profile resource even when it is not selected;
the project identity additionally records whether the contract was selected.

Injected context appends an explicit selected-profile pointer and instructs the
agent to consult it before implementation when applicable. The full profile is
not injected. Without an explicit selection, no profile is activated. Implementer and
reviewer compare the same expected identity, including this selection.

Omitting profile options on configure or upgrade preserves the current choice.
Changing a configured choice requires `upgrade-installed --profile architecture`
or `upgrade-installed --clear-profiles`, with preview then `--apply`. The latter
returns to generic guidance. Initial schema-1 pins without a `profiles` field
remain generic and retain their exact identity until an explicit upgrade writes
the expanded pin. They still require the exact matching installed package.

### Optional recorded lint pairing

Architecture guidance alone is allowed. Without an explicit pair, status and
context say **`Lint contract: unrecorded`**; no linter installation is inferred.
To record a pair, first independently locate the consumer's actual resolved
`dart_architecture_lints` source and verify its identity/configuration there.
Do not select a different/latest checkout to make a mismatch disappear.

From that selected linter checkout, the owner can explicitly run its exporter:

```sh
dart run tool/generate_rule_tables.dart --check --guidance-root GUIDANCE_PAYLOAD --export-contract CONTRACT.json
dart run tool/generate_rule_tables.dart --verify-contract CONTRACT.json
```

These are documentation for owner-approved source verification, not commands run
by guidance hooks. `GUIDANCE_PAYLOAD` is the matching guidance payload directory;
keep the artifact outside its source inputs. Follow the linter's
[paired-contract specification](https://github.com/Gaan21/dart-architecture-lints/blob/main/docs/paired_contract.md)
for the exact schema and source manifest. Exporting self-attests that checkout;
it does **not** prove an application installed or ran it.

Then preview/apply the explicit pairing:

```sh
flutter-guidelines configure --installed --profile architecture --repo PROJECT --lint-contract CONTRACT.json
flutter-guidelines configure --installed --profile architecture --repo PROJECT --lint-contract CONTRACT.json --apply
```

For an existing pin, use `upgrade-installed --repo PROJECT --lint-contract
CONTRACT.json` instead, then `--apply`. Omitted contract options preserve the
embedded pair without rereading the old artifact. `--clear-lint-contract` explicitly
removes it. Changing a pair through configure is refused. Clearing the architecture
profile also requires clearing its lint contract in the same explicit upgrade.

The portable pin embeds the complete contract and its canonical SHA-256, never
the input artifact's machine path. The contract records source package/version,
profile, source-manifest digest, all 51 diagnostic IDs, booleans, exact options and
severities. Validation checks exact IDs/enabled states against the installed
guidance table, selective typing policy, strict JSON shape and bounded values.
Other local options/severities are preserved as declared, not interpreted as a
proof of detector behavior. Contract canonicalization matches the exporter:
recursively UTF-16-sorted keys, preserved arrays, compact UTF-8 and one LF.

Expected project identity includes the entire pair, so a reviewer on another
machine checks the same contract without needing the original artifact path.
Status/context show its digest, source digest and package version, explicitly
**recorded, not installed-runtime verified**. Guidance performs no Dart execution,
dependency resolution, lockfile inspection or runtime attestation. Actual installed
source and effective consumer configuration still need independent verification.

Installation on a machine is not a project pin. On another machine, check out
the versioned pin, install the matching package and run `install --repo PROJECT`
(preview, then `--apply`). The export is recreated from installed resources;
nothing is fetched from Git. `status`/`doctor --expected SHA256` and injected
context expose/check the portable identity. A reviewer should retain the expected
identity with the reviewed revision and compare it, rather than resolve latest.
Local native instructions remain part of the project revision under review, not
part of this public package identity. The artifact task API still locks its
source/bundle/policy/overlay identity at preparation.

## Connection and delivery

`install` defaults to both clients; `--runtime claude|opencode` selects one.
All mutations require `--apply`. Apply writes:

- Claude: two command hooks in `.claude/settings.local.json`, for SessionStart
  and UserPromptSubmit, calling the selected tools interpreter with `-I`.
- OpenCode: `.opencode/plugins/flutter-guidelines-installed.js`, invoking that
  interpreter without a shell during the system transform.
- `.flutter-guidelines-installed/connection.json`, recording owned hook/plugin
  identity; `.gitignore` entries for local files.

Claude SessionStart injects the entry page, identity and verified guidance-root
path. UserPromptSubmit repeats only the provenance/identity and selected-profile
pointer, keeping the full entry out of each prompt. OpenCode system transforms
include the entry and replace their previous injected block. Relative detail
links refer to the guidance root. No local instruction discovery,
policy snapshots, Git fetching, subprocess package installation, work state,
leases, session-release events or tool-write guards occur during delivery.
Editing native `AGENTS.md`/`CLAUDE.md` does not invalidate the tool. Existing
conversations still contain already-delivered instructions after any change.

Every delivery checks installed identity, the complete export and owned connection.
The OpenCode request also checks its loaded adapter fingerprint. Failure warns
without fresh injection and does not block ordinary conversation/tool access.
An in-place package upgrade mismatches the old project pin until explicitly
approved. Prefer updates between review cycles, with clients restarted afterwards.

Only selected clients are inventoried and connected: an unused client's loaders,
configuration and disable flags do not prevent a single-client connection.
Requests from an unselected runtime warn without injecting guidance.
Other Claude entry hooks, recognizable instruction-injecting hooks in any event,
OpenCode plugin/instructions configuration and recognizable instruction plugins
are reported as possible competitors. Ordinary guards can change or
be removed without persistent guard attestations. Unrelated settings are merged
and preserved. Static detection cannot prove the behavior of arbitrary scripts;
owners must inventory custom/global loaders and client-managed configuration.
Native project/folder guides are intentional local authority, not competing
public payloads. This is integrity checking, not a same-user security sandbox.

`uninstall` previews/removes owned entry hooks and the plugin, preserving unrelated
edits. Pin, immutable exports and ignore entries remain. A changed owned hook or
plugin causes refusal for inspection. There is no need to close a work or release
a session in installed mode. Reload clients after connection changes.

## Explicit updates and rollback

1. Select and install the owner-approved exact package separately. Retain the
   previous wheel/environment. This may be an explicitly approved development
   source trial; hashes do not establish publisher trust.
2. Run the **new** executable's `upgrade-installed --repo PROJECT` preview.
   It shows old/new pins and connection diffs without selecting a remote source.
   Profile selection is retained unless explicitly changed with `--profile
   architecture` or `--clear-profiles`.
3. Review, then repeat with `--apply`. A new immutable export is created and owned
   connections are refreshed to the new interpreter. Old exports stay intact.
4. Review/commit the pin normally and reload affected clients/contexts. Verify
   `status --expected SHA256` in both implementation and review environments.

To roll back, install/use the previous exact wheel/environment and repeat the
same explicit preview/apply operation. Do not edit export files or replace their
contents in place. A partially interrupted install/update is detected by identity
or connection verification; inspect the recorded connection and restore the
previous exact hook/plugin from the preview before retrying. There is no automatic
repair or executable updater. When switching client selection, uninstall the
current connection, then install with the new `--runtime` selection.

## Legacy migration

Migration is an owner operation, not executed by this implementation:

If old work is `rebaseline-required`, `end` cannot close it. Report this before
attempting migration. Editing indexed native instructions can cause this state.
After explicit approval, follow the old runtime's
[local-policy rebaseline procedure](runtime.md#local-policy-rebaseline): exit actual
sessions, release only confirmed-exited sessions, preview/apply rebaseline with the
original CLI, then rejoin the replacement identity and renew validation before
acceptance and closure. Migration planning does not perform these actions itself.

1. Retain the old tools environment and its original CLI. Check old `status` and
   any outstanding work/review before changing configuration.
2. Complete acceptance, run legacy `end`, exit all clients, and verify leases
   released. Follow legacy recovery for genuinely stale sessions; do not erase
   work state or edit live snapshots to bypass closure.
3. Preview/apply `uninstall` **with the old CLI**. If owned files changed, inspect
   their backups and reconcile deliberately using the legacy procedure.
4. Archive the legacy `.flutter-guidelines.json` outside its active filename.
   Keep old state/exports as evidence. Remove any old manually installed loaders
   or imports explicitly after review. Existing WorkTracker deployments are not
   changed by installing this package or by these documentation changes.
5. Install the selected new package into a tools environment. Preview/apply
   `configure --installed`, then `install`. Review/commit the portable pin.
6. Restart clients and verify injected identity, mismatch warning behavior and
   native local scope separately in each installed client.

Installed configuration refuses an active legacy configuration or installation
record. Legacy APIs retain their existing semantics. Do not mix loaders; merely
installing a new wheel does not authorize migration or consumer activation.

## Evidence limits

Python subprocess and direct Node tests exercise the new controller/adapter, with
resource and clean-install checks in `tests/check_distribution.py`. They do not
establish installed-client event support or warning visibility. Real Claude Code
and OpenCode trials are still required for startup/prompt/system transforms,
resume/compaction and folder-scoped native instructions. No native enforcement
claim follows from these tests. Only tested runtimes/platforms may be reported.
