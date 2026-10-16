# Project choices and update review

## A simple mental model

The guidance package is written engineering advice plus agent delivery. The lint
package is executable analysis. Local instructions describe a project's concrete
architecture and product. They collaborate; none silently configures the others.

The owner approves a selection for a repository. An agent reads that selection,
checks actual installed controls and follows the relevant local scope. Repository
names, a company-word in a diagnostic ID, and files sitting in a cache do not
select a product contract.

## Choose a contract for a new project

1. Select an exact guidance package and record its identity using
   `configure --installed`. With no profile, only generic common guidance applies.
2. If adopting the stricter architecture, select `--profile architecture` during
   configure. This includes strict class-containing variable names, getter-first
   member order, selective types and the documented architecture conventions.
3. Independently add and lock the chosen lint dependency in the Flutter package.
   Review its generated `profiles/architecture.yaml`, `profiles/style.yaml` or
   `profiles/legacy.yaml`, then merge the chosen selection into that package's
   `analysis_options.yaml`. Preserve its official include chain and existing
   severities, scopes and exception policy. Profile files are samples, not a
   subscription: editing an upstream sample does not rewrite a consumer.
4. Record the selected architecture, product contracts and approved deviations in
   the project's native instructions. Keep folder-only contracts in their folder.
5. Run the project's approved analyzer/lint/behavior checks. A YAML key or installed
   dependency alone does not prove a rule exists, runs or has the desired severity.
6. Optionally record the stock architecture lint contract with guidance as described
   in [installed mode](installed-mode.md#optional-recorded-lint-pairing). Verify the
   actual resolved lint source independently first.

The guidance CLI currently offers only the `architecture` profile. The linter's
style and legacy samples are **not** guidance CLI profiles. All 51 lint diagnostics
remain individually selectable; the new architecture recommendation enables 48,
while legacy defaults retain all 51.

## Per-rule activation

In custom_lint 0.8.1, selection belongs in a list; rule options are sibling keys:

```yaml
custom_lint:
  enable_all_lint_rules: false
  rules:
    - method_order: true
    - variable_name_should_contain_class_name: true
    - require_explicit_types: true
      policy: selective
    - domain_entities_must_use_freezed: false
```

This intentionally partial example enables only three custom rules. It is **not**
the full architecture selection or a migration template. Severity overrides go
under `analyzer.errors`; `warning` is not an enable/disable value. See the linter's
[configuration documentation](https://github.com/Gaan21/dart-architecture-lints/blob/main/docs/configuration.md)
for the parser and each detector's supported options.

If a product deliberately uses immutable values without that generator, its local
instructions must explain the disabled generation rule and the chosen alternative.
Another product can retain it. Both can use the same common package without copying
one product's APIs into public guidance. Changing a rule changes policy and needs
review, even when only one line of YAML changes.

The recorded lint pair currently requires the stock 48-rule architecture selection
and selective typing. It rejects different enabled states; it is not a general
custom-profile engine. For a custom selection, retain the exact dependency lock,
effective configuration and local deviation policy in version control and report
that agreement manually. Do not attach the stock contract and label custom rules
verified, or clear an existing pair without explicit approval.

## How an agent knows the product

The project pin tells it the shared guidance/profile. Root native instructions tell
it the local authority, commands and architecture. Folder guides apply to relevant
paths, not unrelated folders. Referenced product knowledge supplies business rules.
The effective lint configuration identifies executable checks, their scopes and
options. A selected rule's public name does not identify a tenant or product.

For example, one application's dates may display in a business zone and another's
in the device zone. The shared principle is to follow the intended time contract;
local instructions and configured converters/scopes provide the actual choice.
The agent must report contradictory or missing choices rather than invent one or
weaken a local contract to match a generic example.

## Agent update review

When asked **"The Flutter guidelines package changed; review it"**, perform this
bounded review before making installation or policy changes:

1. **Find the active mode.** An installed-mode pin is
   `.flutter-guidelines-installed.json`; a legacy configuration is
   `.flutter-guidelines.json`. Inspect the project's existing executable/launcher,
   native connections and recorded status. Do not assume the current upstream
   README describes the installed mode. Both active configurations are a conflict.
2. **Record the current pair.** Guidance identity/profile, lint package identity from
   the lockfile and resolved source, effective options/severities, local instruction
   revision, and checks previously established. Missing evidence stays unknown.
3. **Identify the candidate.** Inspect source changes/release notes read-only and
   name an exact commit or release. A moving branch may be inspected to discover a
   candidate; freeze it before implementation and review. Do not resolve latest
   independently for different participants. Do not build, install or execute the
   candidate just because reading the changes was requested.
4. **Classify impact.** Content only; controller/adapter; lint implementation or
   options; architecture policy; local product contracts; or legacy-to-installed
   migration. Explicitly list any rule enabled/disabled, severity changes, and
   examples or application code that would change. Preserve local protections.
5. **Report and propose.** Current versus candidate identity, relevant changes,
   compatibility, required validation, exact preview/apply plan and rollback source.
   State what remains unverified. A review request authorizes no package upgrade,
   pin change, profile switch, lifecycle closure, Git publication or activation.

A legacy automatic channel remains capable of selecting a newer revision at its
existing work boundary. A review request does not pause that earlier approval.
Report this distinction; any hold/pin or migration is an explicit owner operation.

## Agent request: update the Flutter guidelines

An explicit **"Update the Flutter guidelines; there are changes"** authorizes a
routine installed-mode update, not just a proposal. Complete the steps below
without asking again for the same routine package/pin/connection permission.
It does not mean "perform this update now" when the user is merely discussing
the desired workflow or asking you to edit documentation.

1. Inspect the actual mode, project pin, approved source/update policy, connection
   and existing local changes. Do not mix legacy and installed mode. A legacy
   connection requires its one-time migration/lifecycle, not this routine update.
2. Use the explicitly requested candidate if supplied. Otherwise fetch the approved
   source's update branch once; this package's documented development-source default
   is `https://github.com/Gaan21/flutter-agent-guidelines.git`, `refs/heads/develop`.
   Record its full commit and retain it throughout install and review. A project's
   more specific approved source/ref wins; do not change publishers or resolve
   latest independently in another session. A wheel/local checkout does not fetch
   latest by itself.
3. Inspect relevant changes for compatibility with existing selections. Preserve
   profiles, per-rule choices, options, severities, local product contracts and lint
   dependency unless its change is specifically necessary and authorized. If the
   new guidance conflicts with them, report that new decision instead of changing
   architecture or clearing a recorded pair to make the upgrade succeed.
4. Keep the old exact wheel/environment. Build/install the exact candidate into a
   separate tools environment, then use its `upgrade-installed` preview and apply
   path below. If the candidate is identical, report that no update is needed.
5. Run the approved package/connection checks and applicable project checks. For a
   guidance-only change, do not invent product-wide refactoring or an E2E matrix.
   Compare identities for implementation/review and retain rollback material.
6. Report previous/new identities, preserved selections, check results and the
   exact remaining user action. Agents may not be able to restart their own native
   clients: say "installed; restart verification pending" until that is observed.
   Do not claim a running conversation adopted fresh instructions. Git commit/push
   and release still follow the project's separate authorization.

Ask only for a genuinely new decision or a step blocked by the actual environment
or policy. A missing source approval, incompatible contract, unapproved lint upgrade
or a legacy migration is such a boundary. Normal preview/apply commands are not
repeated approval requests after the owner has already requested the update.

## Apply an approved update

For **installed mode**, after approval and between review cycles:

1. Retain the old exact package/environment, pin and lint lock/configuration for
   rollback. Build/install the approved exact guidance candidate in a tools
   environment, preferably separate from the old one.
2. If required, update the lint dependency to the approved exact source and merge
   reviewed rule/options/severity changes. Do not replace the entire configuration
   with an upstream sample. Run the approved project lint and behavior checks.
3. If using a recorded stock pair, export it from the verified candidate lint source,
   compare against the resolved source/effective selection and retain the artifact.
   This export does not inspect or attest the consuming application by itself.
4. Use the new guidance executable's preview:

   ```sh
   /absolute/new-tools/bin/flutter-guidelines upgrade-installed --repo "$PROJECT"
   ```

   Add `--lint-contract CONTRACT.json` if the recorded pair changes. Omitted profile
   and pair options preserve the old choices. An unchanged incompatible pair must
   be resolved explicitly; do not silently remove it to make the update pass.
5. Review old/new pins and connection diffs; repeat with `--apply` when authorized.
   Review/commit the versioned pin and any changed lint/local-policy files under
   the project's Git authorization. This does not grant publication automatically.
6. Restart/reload selected clients. In new contexts verify the same injected identity
   as `status`/`doctor --expected`, selected profile and native folder scope. Review
   uses the same project revision and exact package. Retain old exports intact.

For **legacy mode**, first use the old installation's documented lifecycle and
recovery. Migrating needs accepted work, actual session exit, old-CLI uninstall,
explicit archival of the legacy configuration and new installed-mode setup. The
[migration procedure](installed-mode.md#legacy-migration) is not a routine package
update; do not execute `upgrade-installed` against a legacy configuration.
