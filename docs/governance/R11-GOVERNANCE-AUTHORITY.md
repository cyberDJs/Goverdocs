---
id: GOV-0005
type: governance
title: R11 Governance Authority / Multi-Actor Trust
status: active
owner: GOVERDOCS
created: 2026-08-17
updated: 2026-08-17
version: 1.0.0
canonical: true
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - GOV-0004
source_refs:
  - GH-ISSUE-35
last_verified: null
review_due: null
---

# R11 — Governance Authority / Multi-Actor Trust

## Purpose

R11 separates approval validity from governance authority. R10 remains responsible for proving that an approval is trusted, fresh, exact-subject bound to repository + PR + HEAD + change digest, and not revoked. R11 evaluates whether the already-verified approvals collectively have enough independent authority to permit a sensitive change.

The R9 required check remains the server-side enforcement boundary. R11 must therefore execute before `GOVERDOCS Governance Gate` is published.

## Canonical authority policy

Policy: `policies/AUTHORITY_POLICY.yaml`

Version: `1`

Roles and capabilities:

- `project-owner`: `approve:standard`, `approve:critical-owner`, `revoke:own`
- `independent-reviewer`: `approve:standard`, `approve:critical-independent`, `revoke:own`

For an approval-required obligation whose matrix severity is `critical`, all of the following are required:

1. at least two distinct authorized actors;
2. at least two distinct authority roles;
3. the PR author is excluded from critical approval authority;
4. capability `approve:critical-owner` is present;
5. capability `approve:critical-independent` is present;
6. one GitHub identity cannot satisfy multiple authority roles for the same critical obligation.

Non-critical approval-required obligations preserve the existing matrix approval semantics.

## Trust composition

The evaluation order is fixed:

1. acquire exact GitHub ChangeSet and PR observation;
2. evaluate the existing deterministic governance gate;
3. generate/verify approval records using existing R10 exact-head and revocation semantics;
4. consume only approval inputs whose gate assessment is `VERIFIED`;
5. apply R11 role/capability/quorum/separation policy;
6. re-check PR HEAD and base against the evaluated subject;
7. build and publish the required `GOVERDOCS Governance Gate` check.

If the authority policy is absent, malformed, references unknown bound roles, or the PR subject changes during evaluation, the authority runner fails before publishing the required check. Under the R9 ruleset this is fail-closed because merge remains blocked by a missing required check.

## Blocking authority gaps

R11 may add these blocking gaps:

- `AUTHORITY_ROLE_ALIAS_CONFLICT` — one actor appears under multiple roles for the same critical obligation;
- `AUTHORITY_QUORUM_REQUIRED` — fewer than the configured number of eligible distinct actors remain;
- `AUTHORITY_SEPARATION_OF_DUTIES` — fewer than the configured number of distinct authority roles remain;
- `AUTHORITY_CAPABILITY_REQUIRED` — a required critical authority capability is absent.

These gaps are part of the existing GateReport `evidence_gaps` list, so the existing GitHub Check mapping remains unchanged: any blocking gap produces `BLOCKED` / check conclusion `failure`.

## Current enrollment reality

At the R11 implementation baseline the repository has one collaborator: `nulleimy`, with repository admin access. No second independent GitHub identity is currently enrolled.

Therefore R11 can prove the negative fail-closed path immediately, but it MUST NOT claim a fully verified positive two-actor quorum until an additional real GitHub identity is enrolled and explicitly role-bound as an independent authority.

The absence of a second actor is an external enrollment blocker. It is not permission to reduce quorum, allow self-approval, alias one actor into multiple roles, or weaken ruleset `20928616`.

## Acceptance gates

R11 implementation is canonical only when:

- authority policy validation is fail-closed;
- unit tests cover quorum, self-approval exclusion, role aliasing, missing capabilities, unverified/revoked records, valid two-actor semantics, and backward compatibility for non-critical approvals;
- the live governance workflow invokes the authority-aware runner from canonical base code;
- quality and CodeQL pass on exact head;
- canonical governance has zero blocking gaps for the implementation PR under the pre-R11 base contract;
- the implementation merges using an exact-head guard;
- post-merge quality and CodeQL pass;
- ruleset `20928616` remains strict and unchanged.

R11 negative enforcement is verified only when a real critical probe with the currently enrolled solo actor remains `BLOCKED` and GitHub rejects its exact-head merge server-side.

R11 full verification additionally requires a positive live critical probe with two distinct real non-author actors covering both required critical capabilities. Until then the status is `ENROLLMENT_BLOCKED`, not `VERIFIED`.
