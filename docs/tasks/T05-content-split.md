# T05 — Lossless common/private content split

Status: pending. Depends on: T01 + T02. Executor: consumer agent with private access.
Read [handoff](README.md), scope architecture/preservation requirements and bundle
schema accepted in T02. May run alongside T03/T04 in separate owned workspaces.

## Goal

Prepare common guidance and the private `worktracker-architecture-guides` bundle
without losing, weakening or accidentally publishing any existing guidance.

## Inputs and boundaries

- Owner-selected Git account/workspace/access and explicit authorization before
  creating the new private repository or publishing anything to either source.
- Actual common payload, selected existing architecture profile, WorkTracker's
  root/folder instructions, exceptions and referenced contracts, at recorded inputs.
- Keep originals and the current functioning connection. Do not change active
  instructions or reclassify the whole current profile by renaming it.

## Work

1. In private evidence, inventory every rule, exception, topic and required link.
   Record its source, destination, retained meaning and verification method.
2. Classify clearly reusable guidance as common. **If uncertain, place it in
   WorkTracker.** Resolve contradictory/overlapping prose explicitly; do not drop
   requirements during deduplication, summarization or formatting.
3. Prepare complete bundles with short entries, authored reading conditions,
   preserved detail links/notices and explicit inventory. No extra profile
   activation or custom dependency machinery.
4. Check public output for private paths, product APIs and product-specific rules.
   Publish no private classification report or logs in the common/tool repositories.
5. Verify every inventoried requirement has a destination and every required local
   reference is present. Compare meaning as well as file hashes where text moved.

## Acceptance

Private source-to-destination coverage has no unassigned or discarded requirements;
uncertain cases are retained privately. Common and WorkTracker bundles pass T02's
schema/link/inventory verification. Review confirms conditions/modality, exceptions,
offline durable-local acceptance and attribution remain intact. Changing delivery
does not install/change executable lints or refactor the product.

The old payload is not deleted or the live consumer switched here. Agree any later
retirement with T06 after validated migration; preserve rollback source/evidence.

## Handoff

Privately record exact candidate sources and selections for T06. Public handoff
reports only readiness/coverage outcome, not product content. Completion evidence: pending.
