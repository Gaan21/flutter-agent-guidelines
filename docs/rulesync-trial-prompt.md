# Product-agent handoff: evaluate rulesync

Copy the instruction block below to the product repository's agent, providing
the exact published guidance commit to evaluate. The prompt does not require a
permanent migration. See [the preparation recipe](rulesync-trial.md).

---

Evaluate rulesync as a replacement for the custom Flutter guidance delivery in
this product. Follow this repository's AGENTS.md first. Use actual Claude Code
and OpenCode sessions; generated files alone are insufficient evidence.

## Preparation materials

Use an existing checkout of `https://github.com/Gaan21/flutter-agent-guidelines`
if it contains the exact commit supplied by the owner; otherwise obtain a
disposable checkout outside the product. Do not reset or switch a dirty shared
checkout. Fix that commit once for the whole trial, including review. Read:

- `docs/rulesync-trial.md` for the tested export and tool-installation recipe.
- `docs/simplification-review.md`, especially the rulesync-first direction.
- `tools/export_rulesync_trial.py`, the disposable export helper.

If the owner did not supply an exact commit, resolve the approved `develop` ref
once and record its full commit before preparation. If that revision lacks these
files, report the mismatch rather than silently selecting another revision.
Do not edit the guidance repository during the product trial.

## Owner choices

- Suggest technology modules and directory scopes, confirm and persist selection.
- Start with one shared content release and activate only selected modules.
- Explicit local product decisions override common recommendations.
- Keep guidance separate from dart-architecture-lints and executable lint choices.
- Never update guidance automatically on client startup or separately per role.

Only Flutter content is supplied today. Use its existing selected profile;
generic is not equivalent to an existing architecture selection. Do not download
unrelated third-party rule collections or invent production modules.

## Authorization and boundaries

The owner authorizes a local, reversible product integration trial and checks in
both installed clients using their ordinary available service access. Do not
read/copy secrets or change global configuration. No staging, commits, pushes,
releases, registry publishing, deployment or product-feature implementation.
Do not leave the trial active as a permanent replacement.

Inventory current instruction files, loaders, hooks, guards and dirty files.
Preserve unrelated changes. Avoid delivering the same guidance through both the
old adapter and rulesync. If disabling the old delivery requires destructive
migration, an active-task snapshot edit or changing unrelated protections, stop
that integration and explain the blocker. Do not weaken guards to force success.

## Execute

1. Record installed client, Node/npm and Python versions. Select one exact
   approved guidance commit and rulesync 36.0.2. Retain the npm lockfile; do not
   resolve latest for review or substitute development-only documentation.

2. Use the documented helper to export into a new temporary workspace outside
   this product and the guidance checkout. Install rulesync into a separate
   disposable tool directory, with a private npm cache and lifecycle scripts
   disabled. Use a clean environment for generation, not copied credentials.

3. Generate only rules in that workspace. Inspect the two generated root files,
   source inventory, selected profile and entry-link transformation. Verify raw
   payload copies against the selected commit. Retain the manifest digest outside
   the workspace. Repeat generation and compare bytes.

4. Prepare a reversible product integration with an exact record of owned
   changes. Preserve existing root/folder instructions; never blindly copy the
   generated AGENTS.md or CLAUDE.md over them. Copy the accompanying payload to
   the referenced location and integrate the generated entry deliberately.
   Detect whether both root files or the previous loader cause duplicate loading.
   Count the manual work; this recipe does not claim one-command installation.

5. Start fresh sessions in each client. Capture available loading diagnostics
   and observable behavior: selected entry, relevant topic access, preserved local
   authority, two folder scopes and existing guard coexistence. Use clearly
   labelled disposable scope markers if needed. A model echoing an identifier
   is only a smoke test, not proof of the complete delivered context.

6. Check resume and compaction separately where possible. If you cannot launch,
   inspect or reload a client from this environment, give the owner one concrete
   manual action and mark the check pending. Do not silently nest an unsupported
   client session or declare simulated harness checks to be native validation.

7. Test missing/modified generated entries and lazy-loaded topic files in the
   disposable workspace, not active product instructions. Distinguish output
   drift checks from runtime tamper handling. Do not claim the trial manifest
   enforces anything in the clients. No task approval record is fabricated.

8. Assess prepared offline operation. If a real network-denied environment is
   available, run preparation-independent checks there without credentials.
   Otherwise mark offline isolation untested. Guidance availability does not
   imply offline model inference. Check update behavior in a separate export
   using another approved source only if available; otherwise record it pending.

9. Restore the prior product integration and confirm unrelated files/settings
   remain intact. Delete only the trial resources you created after retaining
   necessary non-secret evidence. Do not remove pre-existing environments.

## Deliver in plain Spanish

- What rulesync replaced and what custom code or manual steps remain.
- Exact tested versions, selected profile, source revision and inventory digest.
- Counted install/update steps, machine prerequisites and restart needs.
- Per-client table: passed / failed / pending, with evidence and limitations.
- Factory fit: same prepared source/bundle/policy/overlay identity for implementer
  and reviewer, before commands enter a network/credential-free sandbox.
- Recommendation: adopt, add a small trusted-host check, or reject.
- Reversibility result and any files retained for the owner's review.

Keep private paths, product APIs, logs and reports in the product's authorized
evidence location. Propose only sanitized conclusions for the public guidance
repository. Keep source-file identity distinct from rendered-entry identity and
actual client delivery; none establishes model obedience.
