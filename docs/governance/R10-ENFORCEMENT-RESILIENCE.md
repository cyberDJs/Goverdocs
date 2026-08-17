---
id: GOV-0004
type: governance
title: R10 Enforcement Resilience / Bypass and Failure-Mode Proof
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
  - GOV-0002
source_refs:
  - GH-ISSUE-27
last_verified: 2026-08-17
review_due: null
---

# R10 — Enforcement Resilience / Bypass & Failure-Mode Proof

## Purpose

R10 proves that the R9 required governance gate remains fail-closed when the repository is exposed to stale state, missing checks, approval lifecycle changes, and failing required-check execution.

The authority for every negative proof is GitHub's server-side branch update or pull-request merge rejection. A local evaluator result alone is not sufficient.

## Canonical baseline

Repository: `nulleimy/Goverdocs`

Protected target: `refs/heads/main`

Required status check: `GOVERDOCS Governance Gate`

Expected producer: GitHub Actions integration `15368`

Active ruleset: `20928616`

Strict required status checks policy: `true`

Bypass actors: none.

## R10 invariants

### R10.1 — missing-check fail-closed

A new commit that cannot already possess the required governance check must not be able to update `main` directly.

### R10.2 — stale-branch fail-closed

A pull request whose required check succeeded against an older base must become unmergeable after `main` advances until its branch is brought up to date and reevaluated.

### R10.3 — approval/head binding

A project-owner approval for exact head `H1` must never authorize a different head `H2` after the pull-request branch changes.

### R10.4 — approval revocation

If an accepted project-owner approval is dismissed or otherwise revoked, the governed pull request must return to a blocking state.

### R10.5 — required-check failure fail-closed

A failing execution of the required governance-check context must prevent merge even if other checks or evidence are green.

## Proof discipline

Each proof must preserve these controls:

- no ruleset weakening;
- no bypass actor;
- no force merge;
- no direct update that succeeds without the required check;
- exact-head merge guards where a positive merge is expected;
- temporary negative proof branches are closed unmerged;
- canonical repository changes are merged only after quality, CodeQL, governance and review-thread verification.

## Initial evidence

R10.1 has already demonstrated that GitHub rejects a direct `main` update when the required check is absent. The server returned a repository rule violation stating that `GOVERDOCS Governance Gate` was expected.

R10.2 through R10.5 remain proof obligations until their live GitHub evidence is recorded in issue `#27` and this document is reconciled.

## Completion condition

R10 is complete only when all five invariants have live server-side evidence and the final `main` remains covered by ruleset `20928616` with the same or stronger required-check policy.
