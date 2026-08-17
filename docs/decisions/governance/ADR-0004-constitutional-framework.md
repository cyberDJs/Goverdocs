---
id: ADR-0004
type: architecture-decision
title: Establish a Constitutional Framework with Scoped Operating Modes
status: accepted
owner: GOVERDOCS
created: 2026-07-26
updated: 2026-08-17
version: 1.0.1
canonical: true
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - CONST-FRAMEWORK-GOVERDOCS
  - PRODUCT-MODE-GOVERDOCS
  - WB-0003
  - REV-0003
  - GOV-0001
source_refs:
  - SESSION-2026-07-26-01
  - SESSION-2026-07-26-02
  - GITHUB-MAIN-b002135d4ce532c451bf6eee9cd9c8782431ee92
  - GITHUB-RELEASE-v0.1.0@018d8b7d5f5ab12f537991fe565b9dae4af3b0d9
last_verified: 2026-08-17
review_due: 2026-09-17
---

# ADR-0004: Establish a Constitutional Framework with Scoped Operating Modes

## Context and problem

Two large independent constitutions would duplicate the motto, truth statuses,
approval gates, zero-trust rules and change-gate definitions. Duplication would
create governance drift and conflicting sources of truth.

The existing WORLD constitution is immutable and checksum-locked. This bounded
change must not modify its bytes or silently change its authority.

## Decision

Adopt a coordinating constitutional framework subordinate to WORLD, a scoped
product/decision/execution operating mode and one machine-readable 10-of-10
change-gate policy. The framework is the single source for approval gates; the
YAML policy is the single source for the ten change-gate dimensions and refers
back to the framework instead of duplicating the gate list.

The first integration is `warn-only`. It validates structure and integrity but
does not create an autonomous writer or a release operation.

## Decision drivers

- one canonical source per shared rule and explicit references between sources,
- preservation of the WORLD checksum,
- files-first and CLI-first design,
- deterministic validation,
- small reversible adoption step,
- separate approval gates.

## Considered options

1. Two independent constitutions — rejected because of duplication.
2. One large replacement constitution — rejected as an unsafe rewrite.
3. Coordinating framework plus scoped modes — selected as the smallest
   migration-compatible experiment.

## Consequences

Positive:

- common invariants are defined once,
- product and engineering scopes remain explicit,
- the change gate becomes schema-validatable without duplicating approval gates,
- WORLD remains byte-identical.

Negative:

- the interim authority model still places WORLD above the framework,
- a later promotion or consolidation requires a separate WORLD amendment,
- the first version validates policy structure but does not score real changes.

## Verification and required evidence

- exact WORLD SHA-256 remains unchanged,
- change-gate YAML validates against its schema,
- exactly ten unique dimensions exist,
- the policy references the canonical approval-gate section,
- both exact operational-invariant sentences and required truth statuses exist,
- new documents pass metadata and relationship validation,
- full project tests and deterministic rebuild pass in the canonical worktree.

## Migration and rollback

Apply the bounded patch without commit, regenerate derived artefacts and run all
local gates. Roll back with `git apply -R` before commit or `git revert` after a
separately approved commit. Do not use force push.

## Approval

Status is `accepted` for the bounded `warn-only` governance scope. The accepted
implementation is commit `6236a8cae777063811b41ae00fb36f819f8468e7`. Local implementation, commit and push
were separately approved; quality run `30191576044` and OpenSSF Scorecard run
`30191576042` succeeded for that exact SHA.

Tag, release, deployment, hard enforcement and autonomous canonical writes are
not approved by this decision.

## Revalidation — 2026-08-17

The decision itself remains valid and is not superseded. The original acceptance
and its exact SHA/run evidence remain historical evidence for the bounded
`warn-only` decision.

Current GitHub revalidation was performed against canonical
`main@b002135d4ce532c451bf6eee9cd9c8782431ee92`. A later, separately governed
release `v0.1.0` exists and targets
`018d8b7d5f5ab12f537991fe565b9dae4af3b0d9`. That later release does not
retroactively widen ADR-0004 approval: deployment, hard enforcement and
autonomous canonical writes remain outside this decision.

This revalidation makes no claim about current local Git state. Next review is
due `2026-09-17`.
