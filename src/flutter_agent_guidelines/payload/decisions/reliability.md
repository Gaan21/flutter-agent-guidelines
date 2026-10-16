# Resource and operation reliability

Packaged generic guidance. Concrete protocols belong to the consumer.

## Resource ownership

- Record creator, owner, borrowers, lifetime, transfer and teardown for controllers, streams, subscriptions, timers and platform resources.
- Owners release their resources and perform required parent cleanup on every normal teardown path. Borrowers must not dispose externally owned resources. Verify helper/base cleanup rather than guessing from a missing local call.
- Preserve explicit resource-field annotations wherever installed cleanup detection depends on them. Relaxation requires evidence for inferred/alias/multi-field, borrowed, inherited/helper and conditional/early-return cases.
- An overlay's resources must survive its own lifecycle, including caller removal. Prefer an explicit overlay State owner; reusable scoped search and one-screen form resources can have distinct owners under local contracts. Avoid mixin/static-map ownership without an explicit reviewed lifecycle contract.
- Use the overlay builder's context or previously resolved plain values for inherited lookups. An after-await mounted check addresses an async gap, not captured caller-context validity during later overlay rebuilds.
- Dialog buttons return a result through the dialog builder's context. Await `showDialog`, check the caller's mounted state, then run result callbacks or follow-up effects. Coordinate any further navigation with the route lifecycle.
- Give form exit one owner. Decide whether successful save closes the form or leaves it visible according to the consumer's UX contract; coordinate `PopScope`, callbacks and navigation to avoid duplicate pops. Do not impose one exit interaction on every product.
- Test rapid close/reopen, autofocus, rebuild, caller removal and post-disposal events. Presence of a close/super call is not proof of all-path cleanup or completion.

## Operation completion and concurrency

- Before implementation, record operation key, inputs, result owner, criticality, concurrency policy, stale-result rule, cancellation, retry owner and teardown behavior.
- Await the operation's contracted acceptance before success effects/navigation. Online acceptance may require server confirmation; an approved offline flow may accept a durable local write while visibly pending synchronization. Never present local acceptance as remote confirmation or clear a pending deletion before remote acknowledgment. Critical writes are not fire-and-forget; consume failed outcomes even from nonthrowing Futures.
- Choose latest-result cancellation/discard for replaceable reads, single-flight/shared completion for duplicate writes, and justified independence for parallel reads. Preserve existing per-screen restrictions until an approved operation contract replaces them.
- Cancellation does not necessarily cancel server effects. Define idempotency and late acknowledgment handling; do not assume dropping a Future undoes a write.
- Background work needs explicit noncritical purpose, reason, error owner and reporting/completion policy. Do not hide discarded work in microtasks, timers, wrapper Futures or ignore calls.
- Prevent state notifications from invalidating the tree during build. Where the selected contract forbids detached work in provider construction, defer it through the approved lifecycle seam, with a mounted/lifetime check. Post-frame scheduling is one technique, not proof of correct ownership or a universal ban on asynchronous initialization. Preserve installed disposal and action-handler contracts.
- For overlapping initial load, refresh and retry triggers, share the in-flight Future for the same operation; clear it on success and failure so later retries can run. Refresh returns that completion to its caller.
- Verify the installed justification syntax; a prose reason alone may not satisfy categorized checks. A valid tag does not prove harmlessness or error handling.
- Search debounce duration is a product choice. Test rapid typing, clear, disposal and stale responses with controlled time; do not wire state owners together merely because an old example does.

## Retry and authentication

- Keep one documented retry owner; resolve DataSource/service/repository/coordinator differences before moving behavior.
- Classify transient failures, ordinary client rejection and authentication refresh separately. Bound attempts/backoff, cancellation and idempotency according to the actual protocol; no universal delay table supplied.
- Verify serialized refresh and failure recovery. A check against scattered status-code comparisons does not prove one refresh or safe retry behavior.
- Test timeout, permanent rejection, concurrent refresh, expired credentials, retry cancellation and navigation during failure.

## Offline contracts, when selected

- Choose read/write/synchronization strategy from product requirements; online-only and local-first features need not share one strategy.
- For durable local-write protocols, define local truth, operation identity/metadata, acknowledgment, pending/error visibility, restart recovery and merge rules.
- Preserve pending local changes during remote merges. Use the approved conflict version/timestamp semantics; synchronization bookkeeping time is not automatically a conflict clock.
- Keep deletion evidence until confirmed acknowledgment. A failed delete outcome must not clear pending state or become synthetic success.
- Use transactions for required atomic batches/merges. Storage indexes, journaling, retention, maintenance and pagination thresholds require measured consumer configuration.
- Verify reachability rather than treating network-interface status as proof of service access. Probes, synchronization ordering and budgets remain product choices.
- Test restart with pending writes, pending merge, failed delete acknowledgment, rollback, skewed timestamps, reconnect/auth failure and visible error recovery. Generic offline documentation is not a substitute for these guarantees.
