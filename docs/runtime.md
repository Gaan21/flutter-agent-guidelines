# Automatic local runtime

## Authority and configuration

One Flutter authority plus consumer-local policies. Installed Python controls execution;
Git supplies only allowlisted Markdown and notices, never executable code.
Owner approval of an HTTPS source URL and ref (or full 40-character commit) is
required. A hash proves integrity, not ownership or trust. Approved Git trials
work with development packages; the separate artifact task API retains its
stable-release requirement. No release attestation is implied.

Consumer `.flutter-guidelines.json`:

```json
{
  "schema": 1,
  "source": {"url": "https://example.org/owner/flutter-guidance.git", "ref": "refs/heads/main"},
  "policies": ["AGENTS.md", "CLAUDE.md"],
  "overlays": [],
  "cache": "/absolute/external/flutter-guidance-cache"
}
```

Paths are consumer-relative regular files; existing top-level instruction files
must be listed as policies. Policies retain local authority and are drift-checked;
overlays are read from pinned copies. No generic central catalog is loaded.
`configure` discovers native `AGENTS.md`, `CLAUDE.md` and `.claude/rules/**/*.md`
into the explicit policy list; newly discovered files block existing pins.
Generated/dependency directories (`.git`, runtime state, `.dart_tool`, `.venv`,
`node_modules`, `build`, `__pycache__`) are excluded from discovery. Their policies,
if intentionally used, must be listed explicitly. External delegates are refused.
Cache defaults to `FLUTTER_GUIDELINES_CACHE` or the user cache directory.
Runtime state and work-specific snapshots live in ignored `.flutter-guidelines/`.

### Context and local scope

Claude SessionStart (startup/resume/compact) injects the short entry. UserPromptSubmit
injects only work/source/digest/root/update provenance; PreToolUse verifies and
guards without adding context. OpenCode system transform appends one entry per
model context; prompt/tool verification does not inject another guide.

Only root `AGENTS.md`, root `CLAUDE.md`, `.claude/CLAUDE.md` and explicit `overlays`
are routed as global local inputs. Every declared local file is still snapshotted
and drift-checked. The verified snapshot's `policy-index.json` maps original
consumer-relative logical paths to pinned copies and logical scopes. Nested
AGENTS/CLAUDE apply only along relevant cwd/touched-file ancestor chains.
Claude rules retain native selectors/frontmatter; no glob/YAML selector parser is
claimed. Consult their indexed pinned originals only for applicable paths, with
native loading preserved. Scope is relative to the original consumer tree, never
the snapshot directory. Other explicit policies are indexed for relevant lookup;
use `overlays` for explicitly global private inputs. No unrelated nested rules
are promoted to global instructions.

## Command surface

- `configure --repo ROOT --source-url HTTPS --source-ref REF [--policy PATH] [--overlay PATH] [--apply]`.
- `install --repo ROOT [--runtime claude|opencode|both] [--apply]`: plan by default.
- `uninstall --repo ROOT [--apply]`: remove owned integration only if unchanged.
- `status --repo ROOT`: inspect verified work identity and leases.
- `refresh-check --repo ROOT`: report CURRENT, UPDATE or UNKNOWN; never move pin.
- `end --repo ROOT`: mark closing; finalize only after all leases release.
- `release --repo ROOT --runtime NAME --session ID`: explicit lease release after
  confirming that session has exited; crash recovery is operator-owned.
- `doctor --repo ROOT`: configuration, installed controller and executable probes.
- `inventory-hooks --repo ROOT`: known local/user Claude hook definitions,
  source/event/selector+handler fingerprints and review eligibility; read-only.
- `review-guard --repo ROOT --source SOURCE --digest SHA256 --non-instruction-guard [--apply]`:
  plan/record exact owner-reviewed PreToolUse coexistence before work starts.
- `join --repo ROOT --runtime NAME --session ID --expected DIGEST [--role reviewer]`:
  explicit role receipt; existing work only, never resolve a replacement.
- `hook --runtime NAME`: adapter protocol on stdin; not a user launcher.
- Existing `inspect`, `export`, `verify` and Python artifact task APIs remain.

## Installation

Explicit `--apply` activates only repository-local integration. Claude settings
merge owned hook groups; existing permissions/hooks remain. OpenCode uses an
auto-discovered dependency-free JavaScript plugin, leaving JSONC untouched.
Unknown local/global instruction loaders and external native instruction
delegations require inventory/removal before activation. Global authority files
are conservatively refused; permissions and non-instruction settings remain.
Existing non-instruction PreToolUse guards may coexist after explicit review:
inventory their definition and referenced executable behavior, then attest with
`review-guard`. Config `reviewed_guards` entries contain `source`, `event`
(`PreToolUse` only), `digest`, and `purpose` (`non-instruction-guard`). Fingerprints
cover the canonical group selector/options plus individual command/HTTP handler;
source and event must also match. They do not authenticate transitive script
dependencies. Changed/missing guards invalidate approval. Installation preserves
approved groups structurally and permissions; uninstall restores original bytes.
SessionStart/UserPromptSubmit loaders cannot be waived. Review does not execute
hooks or infer non-instruction behavior from a hash. Unknown guards remain blocked.
After closing work, explicitly remove any superseded `reviewed_guards` entry
before reviewing its replacement; stale approvals are never silently refreshed.
Backups and hashes record owned changes; modified files block uninstall rather
than losing edits. No global settings, tool grants, staging or executable updates.
Restart both clients after installation. Claude requires >=2.1.295 for
`onFailure: block`. Runtime support must be established by actual-version probes.
Uninstall retains owner configuration, work history/snapshots and shared cache.
Restore modified owned files from retained backups before retrying uninstall;
backups are base64 bytes plus hashes in the installation record, never applied
over subsequent edits automatically.

## Work lifecycle

First ordinary session creates a random work identity under a filesystem lock.
The work record and snapshot identify the original consumer worktree; copying
runtime state into another consumer does not authorize a join.
Every runtime/reviewer joins the same source SHA, snapshot digest, local policy
bytes and installed-controller digest. Explicit expected identity joins fail on
mismatch. New conversations reuse the work until explicit closure: no semantic
task guessing, prompt completion detection, idle expiry or hot rebasing.

`end` marks closing while leases exist. Existing sessions may finish; new sessions
cannot join. Last release archives the record and permits the next first join.
Claude SessionEnd is intended to release only the parent process/session lease.
Its parent-PID lease assumption still needs actual native dispatch/resume/child
validation in the controlled consumer trial; subprocess fixtures are insufficient.
OpenCode deletion events and process-exit cleanup are implemented; native delivery
and exit behavior remain trial checks. A returned `dispose` callback is directly
callable in the harness, but native invocation/support is not established by the
config probes and must not be relied on for release. Idle never releases leases.
Concurrent instances retain independent leases. Crashes can require `release`.
Controller/adapter changes during live work fail closed, including already-loaded
adapter hashes. No automatic executable upgrade.

## Failure and integrity

First preparation needs successful remote resolution and exact-commit export.
Live pins resume offline only after complete snapshot/policy/config/controller
verification; failed update lookup reports UNKNOWN, never CURRENT. A moving ref
only produces an update notice. Every prompt/tool guard repeats verification.
Config drift, local policy drift, corrupt state, links, unexpected snapshot files
or mismatched session identities block. Recovery requires operator inspection;
state is never silently reset. Restore changed instructions/controller/config
before release/closure; inspect corrupted state/backups manually. Read-only modes and tool guards discourage writes,
including resolved alias targets; they are not an OS sandbox or shell parser.
Normal restrictive permissions remain effective. Only the short entry and local
policy snapshot paths enter context; decision documents remain focused lookups.

## Upstream contracts

Consulted 2026-10-15: [Claude hook reference](https://code.claude.com/docs/en/hooks),
[OpenCode plugins](https://opencode.ai/docs/plugins/),
[OpenCode configuration schema](https://opencode.ai/config.json).
Fixture protocol tests do not establish real consumer activation or model use.
`doctor` and debug config/agent probes do not prove native lifecycle dispatch,
hook ordering, SessionEnd process ancestry or OpenCode callback disposal. The
trial must validate these before claiming lifecycle enforcement.
