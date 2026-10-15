# On-demand upstream index

External links only; no upstream prose, code or configuration bundled. Topic descriptions below are original navigation notes.

## Reading contract

- Open only the reference relevant to an unresolved decision; stop when resolved. References do not override consumer authority or activate controls.
- Preserve DO/PREFER/CONSIDER and conditional recommendation strength. A project restriction may deliberately be narrower; changing it requires agreement.
- Links are mutable. Evidence available to this guidance was consulted on 2026-10-14; no fresh consultation or latest-resolution claim. Before relying on version-specific APIs, verify the installed version and capture dated evidence.
- Available page labels: Dart 3.13.3; Flutter architecture 3.47, updated 2026-05-05; flutter_lints 6.0.0. These are evidence labels, not consumer upgrade requirements. Configuration main snapshots are not certified published releases.

## Language and analysis

| Topic / section to find | Reference | Scope and caveat |
|---|---|---|
| How to read; Style; Usage; Design/Types | [Effective Dart](https://dart.dev/effective-dart) | Declaration-sensitive typing, errors, async and naming; formatter solves formatting only. Library organization is not a universal one-class-per-file rule. |
| Description; Usage | [flutter_lints](https://pub.dev/packages/flutter_lints) | Dependency plus include and analyzer execution are separate steps; customization allowed. |
| Details | [use_build_context_synchronously](https://dart.dev/tools/linter-rules/use_build_context_synchronously) | Correct mounted object after async gap; not general overlay lifecycle safety. |
| Details | [unawaited_futures](https://dart.dev/tools/linter-rules/unawaited_futures) | Async-body Future consumption; does not prove background error/completion ownership or approve suppressions. |
| Details; Known limitations | [close_sinks](https://dart.dev/tools/linter-rules/close_sinks) | Bounded sink detection; not a universal resource-ownership substitute. |

Inspect the installed lint include chain, actual version, severity and exclusions directly. No vendor configuration or enabled-all template is supplied. A similarly named rule is not equivalent to a consumer obligation.

## Architecture and tests

| Topic / section to find | Reference | Scope and caveat |
|---|---|---|
| Separation of concerns; Handling data; Testing | [Architecture recommendations](https://docs.flutter.dev/app-architecture/recommendations) | Adapt recommendations to context: immutable models strongly recommended; domain layer and separate API/domain models conditional; model generation recommended with alternatives, not a mandate for one generator. |
| Views; View models; Repositories; Services; Optional domain | [Architecture guide](https://docs.flutter.dev/app-architecture/guide) | Responsibility vocabulary; do not equate an upstream service with an installed DataSource or impose a universal Result/base API. |
| Unit; Widget; Integration | [Testing overview](https://docs.flutter.dev/testing/overview) | Cost/confidence and collaboration; no local numeric cap, ratio or coverage baseline inferred. |
| Reading; Writing; Synchronizing | [Offline-first support](https://docs.flutter.dev/app-architecture/design-patterns/offline-first) | Strategy alternatives; not a product outbox, tombstone, retry, company-time or auth protocol. |

## Third-party handling

Linking does not grant rights to copy referenced material. No logos, documentation excerpts, sample implementations, vendor sets or lint sources are included. Any later copy/adaptation requires exact source/version, rights/notice review and authorization; this package supplies no license grant for linked works.
