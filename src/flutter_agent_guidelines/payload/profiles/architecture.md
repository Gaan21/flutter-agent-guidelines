# Selected architecture and strict naming

An opt-in contract, not a universal Flutter architecture. It applies when selected
in the project connection or by local authority. Selecting guidance does not install
or activate a linter. Read the relevant section below before implementation; use
the common decisions and verification procedure for details. Concrete project APIs,
exceptions and operational limits remain authoritative.

## Activation and compatibility

Pair this guidance with the explicit architecture selection of
[dart-architecture-lints](https://github.com/Gaan21/dart-architecture-lints).
The selected contract enables 48 of 51 diagnostic IDs below. The three disabled
language restrictions are intentional; they do not remove architecture controls.
The legacy selection retains all 51 and blanket typing for existing consumers.
Do not replace an existing selection wholesale or infer migration approval.

Record exact guidance and lint identities, selected options, severities and local
exceptions with the project revision used for implementation and review. Inspect
the installed plugin and actual configuration; a rule present only in YAML may not
exist in that installed version. The linter's guidance-root check compares this
table with its real registrations and architecture selection. It does not prove
every behavioral obligation is detected. Its tested configuration documentation,
not historical tutorial snippets, defines the option syntax for that version.

## Names, members and types

- Variable names must contain the relevant class name for nonprimitive types as
  required by the selected detector, including its wrapper and callback exceptions.
  Meaningful role prefixes are welcome; abbreviating a class name is not a substitute
  for this strict contract. A name matching its type is still subject to semantic review.
- Member order is getters/setters, overrides, public methods, private methods.
  Additional ordering of fields and constructors belongs to local policy.
- Use selective explicit types: public fields/top-level variables, public return
  types and public declaration parameters have annotations. Initializing/super
  formals inherit their types. Inferred locals and loops are allowed; explicitly
  annotate inferred `dynamic` and locally configured boundary names. Add annotations
  where they clarify the intended type; inference does not disable static checking.
- Prefer final local bindings when not reassigned. `late`, null assertions and
  related types sharing a file are not categorically forbidden by this selection.
  Review initialization, nullability and cohesion; do not hide contract failures
  behind synthetic defaults merely to avoid a null assertion.

## Architecture and operation contracts

- Keep the selected domain independent of external I/O and presentation types.
  Separate domain entities from serialized models; entities use the selected
  immutable-generation convention, while serialized models expose their codecs.
  Mapping and domain defaults retain separate owners.
- Follow the installed use-case and view-model base contracts and entrypoints.
  Repositories, data sources and use cases preserve the chosen typed-result
  protocol. A lexical no-throw check does not prove a call chain cannot throw;
  preserve the project's distinction between expected failures and programmer defects.
- Keep business decisions and I/O outside widgets. Views use presentation models,
  selected screen contracts and localized copy; simple formatting/visibility can
  remain UI concerns. ViewModels do not own Flutter UI types or contexts.
- Follow the provider naming-order contract while checking actual dependencies.
  Do not introduce ViewModel-to-ViewModel or auxiliary UI-state dependencies where
  the project prohibits them. Infrastructure/settings state may have a distinct
  lifetime and composition root; do not force it into domain use cases.
- Await critical completion before success effects. Preserve Loading-before-await,
  per-layer detached-work prohibitions and per-screen concurrency limits selected
  by the consumer. Operation-specific parallelism needs agreement where it changes
  an existing restriction. Synchronous UI callbacks may await their action contract.
- Detached work has a noncritical purpose, error owner and completion policy.
  When categorized justification is selected, use the exact installed syntax:
  `unawaited-ok: category - reason`. Categories include `dispose-sync`,
  `callback-sync`, `telemetry/logging`, `best-effort-cleanup`, `post-frame-init`
  and `prefetch-noncritical`. A tag does not prove safe failure handling.
  Suppressions also need the installed reason syntax and consumer approval.
- Preserve ownership and parent cleanup for every resource. This architecture
  prohibits resource-owning mixins and static resource maps unless an approved
  local exception supersedes that restriction. Inferred declarations must not
  bypass checks; unsupported ownership/control-flow cases require review.

## Errors, time and UI

- Keep one approved error-reporting owner; do not duplicate reporting across layers
  or remove legitimate technical events merely because they use the same logger.
  Preserve stable localized error codes, structured context and redaction. Verify
  the configured logging API, remote levels, allowlists, deduplication and budgets.
- Keep one authentication-refresh/retry owner according to the installed adapter
  contract. Do not add independent loops in callers. Test failure and concurrency;
  absence of scattered status-code checks is not proof of correct refresh.
- Keep instants, civil dates, clock access and business display zones distinct.
  Configure clock/civil scopes and accepted zone converters explicitly; do not
  permit device-local display where the product requires a business zone.
  Epoch getters are zone-independent. Offline acceptance and synchronization use
  the consumer's protocol, not a generic invented backend contract.
- Use stable identity-based list keys for items whose identity must survive change.
  A fresh unique key or list position is not a stable business identity.
  Use the chosen localization and design-token systems. Ownership/navigation and
  rendered state retention require review and behavior tests beyond AST checks.

## Diagnostic selection and evidence

`enabled` is the recommended architecture selection, not a claim that this package
has activated or executed it. Rule names describe bounded detectors; use the
linked linter's current limitations. General semantics require review and tests.

| Rule | Selection | Obligation / remaining evidence |
|---|---|---|
| `app_exception_must_define_code` | enabled | Selected error-code protocol; check translations and mapping. |
| `avoid_async_in_provider_create` | enabled | Avoid the detected detached initialization pattern; review lifetime. |
| `avoid_async_wrapper_hides_unawaited` | enabled | Do not evade detached-work policy through wrappers; review intent. |
| `avoid_hardcoded_strings` | enabled | Localize applicable user copy; inspect actual localization contract. |
| `avoid_scattered_401_handling` | enabled | Centralize refresh/retry; test concurrent unauthorized responses. |
| `avoid_unawaited` | enabled | Categorized detached-work reason; review errors and criticality. |
| `avoid_unawaited_ignore_without_reason` | enabled | Traceable exception reason; approval remains a local obligation. |
| `datasources_return_result` | enabled | Preserve the selected data-source typed-result signatures. |
| `domain_entities_must_use_freezed` | enabled | Selected generation convention; test actual value semantics. |
| `enforce_final_variables` | enabled | Final local bindings when not reassigned. |
| `enforce_utc_dates` | enabled | Selected instant storage scopes; no epoch conversion ritual. |
| `logger_context_matches_scope` | enabled | Configure receivers/scopes and preserve canonical member context. |
| `logger_context_must_be_structured` | enabled | Structured diagnostic context, not proof of safe contents. |
| `method_order` | enabled | Getters/setters, overrides, public, private. |
| `mixin_no_state_ownership` | enabled | No resource-owning mixins under this selected contract. |
| `models_must_have_json_serialization` | enabled | Codec convention for selected data-model boundaries. |
| `multiprovider_order` | enabled | Selected naming order; also inspect actual dependencies. |
| `no_bang_operator` | disabled | Review nullability instead of a universal assertion ban. |
| `no_business_logic_in_widgets` | enabled | Bounded patterns; review the business/UI boundary. |
| `no_civil_utc_mix_without_helper` | enabled | Configured temporal boundary; names are only partial evidence. |
| `no_device_local_in_presentation` | enabled | Configured business-zone display, including approved exceptions. |
| `no_direct_error_logging_in_data_domain` | enabled | Preserve the selected single reporting owner and exceptions. |
| `no_direct_internet_calls` | enabled | I/O stays in the selected infrastructure boundary. |
| `no_domain_entities_in_presentation_ui` | enabled | Selected presentation-model separation. |
| `no_exception_message_passthrough` | enabled | Do not forward technical errors as user copy. |
| `no_external_dependencies_in_domain` | enabled | Independent selected domain boundary. |
| `no_hardcoded_border_radius` | enabled | Selected design-token convention and configured scopes. |
| `no_hardcoded_color_literal` | enabled | Selected theme/token convention and configured scopes. |
| `no_late_keyword` | disabled | Review initialization rather than forbid all late declarations. |
| `no_local_datetime_constructors` | enabled | Explicit civil/clock exceptions; do not conflate temporal meanings. |
| `no_raw_exception_message_to_user` | enabled | Localized user errors; inspect wrappers and dynamic flow. |
| `no_result_throw` | enabled | Chosen result protocol; inspect capture boundaries and defects. |
| `no_sensitive_data_in_log_metadata` | enabled | Redaction, also reviewed for dynamic/nested data and sinks. |
| `no_serialization_in_entities` | enabled | Keep the selected entity/serialized-model separation. |
| `no_static_map_controllers` | enabled | No static resource registries under this selected contract. |
| `no_utc_time_format_without_empresa_helper` | enabled | Configure approved display converters; generic rule ID only. |
| `one_class_per_file` | disabled | Related public types may share a cohesive file. |
| `overlay_lifecycle_context_safety` | enabled | Builder context and resource ownership; test rebuild/teardown. |
| `repository_methods_return_result` | enabled | Preserve the selected repository result signatures. |
| `require_explicit_types` | enabled | Selective public-boundary/local-name policy, not blanket locals. |
| `require_keys_in_lists` | enabled | Bounded missing-key detection; test identity under reordering. |
| `streamcontroller_must_close` | enabled | Per-owned-field cleanup; review unsupported control flow. |
| `top_level_screens_must_use_base_contract` | enabled | Installed screen contracts, not invented component APIs. |
| `uistate_must_call_super_dispose` | enabled | Required parent cleanup under the selected state contract. |
| `usecases_extend_base_usecase` | enabled | Installed base and generic parameter contract. |
| `usecases_follow_pattern` | enabled | Installed execution/result signature convention. |
| `variable_name_should_contain_class_name` | enabled | Strict relevant class-containing variable names. |
| `viewmodels_call_super_dispose` | enabled | Required parent cleanup; inspect ordering and all paths. |
| `viewmodels_extend_base_viewmodel` | enabled | Installed state/effect base contract. |
| `viewmodels_no_buildcontext` | enabled | UI context remains outside the selected ViewModel boundary. |
| `viewmodels_no_flutter_types` | enabled | UI resource types belong to their selected UI owner. |
