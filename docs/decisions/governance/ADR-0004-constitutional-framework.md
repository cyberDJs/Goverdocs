---
id: ADR-0004
type: architecture-decision
title: Establish a Constitutional Framework with Scoped Operating Modes
status: proposed
owner: GOVERDOCS
created: 2026-07-26
updated: 2026-07-26
version: 0.1.1
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
last_verified: null
review_due: 2026-08-15
---

# ADR-0004: Establish a Constitutional Framework with Scoped Operating Modes

## Context and problem

Two large independent constitutions would duplicate the motto, truth statuses,
approval gates, zero-trust rules and change-gate definitions. Duplication would
create governance drift and conflicting sources of truth.

The existing WORLD constitution is immutable and checksum-locked. This bounded
change must not modify its bytes or silently change its authority.

## Decision

Propose a coordinating constitutional framework subordinate to WORLD, a scoped
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

Status remains `proposed`. Implementation, commit, push, tag and release require
separate approvals.
