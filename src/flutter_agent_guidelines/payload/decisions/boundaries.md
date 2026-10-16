# Engineering boundaries

Apply the consumer's concrete contracts before these packaged generic recommendations.

## Data and dependencies

- Separate presentation concerns, business decisions and external I/O. Repositories may coordinate sources/cache/synchronization where selected; document the boundary instead of treating “only mapping” as a complete architecture.
- Normalize external formats at entry. If separate persistence and domain models are selected, expose the intended types through interfaces; keep serialization in the actual serialized boundary.
- Keep selected mappers deterministic and free of I/O, clocks and invented business defaults. Distinguish rejecting malformed technical input from assigning domain defaults. Preserve mapping failures and field information.
- Define create/update identity explicitly. Do not invent sentinel IDs; verify absent/generated/local/remote identity semantics against the API.
- Prefer immutable values and collection safety. A generator annotation does not prove deep immutability, equality or codec correctness. Generation tools are consumer choices; validate compatibility and nested mutation behavior.
- Use the selected typing and naming policy. Inference retains static types; explicit annotations clarify public contracts or a deliberately chosen type. Do not repeat class names mechanically unless the project's strict naming contract requires it. An activated architecture profile can deliberately be stricter than upstream style.
- Make dependencies and lifetimes explicit at composition roots. Separate borrowed from owned objects; verify factory/singleton lifetime and disposal. Infrastructure settings may have a different lifetime from domain state.
- Put orchestration where the consumer assigns it. Avoid dependency cycles; do not add wrappers or change usecase composition solely to imitate a tutorial.

## Failures and diagnostics

- Preserve the installed public failure protocol, including typed outcomes when selected. Consume both success and failure; never substitute silent null/empty results for failure.
- Verify base methods, generic ordering, inherited entrypoints and internal capture boundaries before using samples. Expected failures and programmer defects need an explicit policy; do not promise universal no-throw behavior from a lexical check.
- Check server rejection envelopes as well as transport success. Preserve original diagnostic context and stack traces when adapting failures.
- Assign one visible error owner per action: persistent state, ephemeral effect or an approved background status. Avoid duplicate state/toast/report paths; do not hide critical failure behind success navigation.
- User copy follows the consumer's localization contract; diagnostic messages are not safe user messages. Stable error identifiers need verified translations and argument semantics.
- Assign one diagnostic reporting owner. Review permitted technical events separately from captured failures. Use structured, redacted metadata; literal-key checks cannot protect dynamic/nested data.
- Verify remote level allowlists, deduplication, rate limits and sink behavior with the actual reporting API. Replacing print with a logger does not establish confidentiality.

## Time

- Separate current-time acquisition, persisted instants, civil/date-only values and display timezone. Use an injectable/testable current-time seam.
- Preserve the consumer's instant serialization and zone conversion contract. Device-local conversion is not a substitute for a business/company timezone.
- Epoch milliseconds identify an instant independently of the DateTime's display zone; do not add conversion solely to read that value. Civil dates and clock adapters need explicit scopes, not a blanket conversion of every date to UTC.
- Keep backend-resolved reporting inputs and date-only exceptions explicit. Missing product time authority blocks contract-changing work.
- Test device/business-zone differences, midnight, DST transitions and serialization round trips. Helper names and redundant UTC conversion syntax do not prove correctness.

## UI capabilities and identity

- Model persistent render state separately from one-shot effects. Verify empty/error states, effect ordering and rebuild replay behavior against the installed components.
- Keep business rules and I/O orchestration out of widgets. Simple visibility, formatting, animation, layout and routing can remain UI concerns where local policy permits.
- Use the consumer's selected screen/shell contracts. Define who publishes contextual actions and who owns chrome; avoid coupling the shell to concrete state owners.
- Prefer explicit typed inputs/callbacks or an approved shared coordination service over hidden provider lookups or state-owner cycles. Parameter presence alone does not prove dependency safety.
- Order providers by actual dependencies and scope ownership. Changes to established ordering, nesting or state-owner isolation require consumer agreement.
- Use lifecycle-capable widgets where resources require them; widget naming alone cannot decide ownership. Preserve approved infrastructure/navigation exceptions.
- Maintain stable row identity across reorder/insert/delete; constructor-key checks do not prove unique stable item keys. Locale keys must not accidentally reset navigation state.
- Preserve settings persistence and routing identity across theme/locale changes. Subscribe at the level needed for correct updates; optimize only from representative profiling.
- Use the existing token, route and localization systems. Verify back/deep-link/modal behavior, save completion and pop interception; avoid unverified routing quotas or breakpoints.
- Do not mix localization systems or migrate argument keys implicitly. Test translated errors and placeholder coverage across supported locales.
