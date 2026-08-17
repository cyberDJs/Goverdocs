---
id: GOV-0003
type: governance
title: R9 Enforcement Proof
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
  - GH-ISSUE-23
last_verified: 2026-08-17
review_due: null
---

# R9 — Enforcement Proof

## Purpose

This document is the governed carrier for the first live hard-enforcement proof of R9.

The repository ruleset under test is repository ruleset `20928616`, targeting `refs/heads/main` and requiring the GitHub Actions check context `GOVERDOCS Governance Gate` from integration `15368` with strict/up-to-date status-check enforcement and no bypass actors.

## Proof protocol

The same exact PR head is used for both sides of the proof:

1. before project-owner approval, the governance check must publish a blocking conclusion and GitHub must reject an attempted merge;
2. after an exact-head `GOVERDOCS-APPROVAL-V1` project-owner COMMENT approval, the governance check must become non-blocking and GitHub must allow the exact-head merge once all required checks are satisfied.

The negative merge attempt is intentional evidence. It must not be bypassed, force-merged, or replaced by a direct push to `main`.

## Acceptance

R9 hard enforcement is considered verified only when GitHub itself demonstrates both outcomes against the active repository rule:

- `BLOCKED` governance state prevents merge;
- approved non-blocking governance state permits merge;
- the successful merge is exact-head guarded;
- post-merge `main` remains covered by ruleset `20928616`.

Execution evidence is recorded in GitHub issue `#23`.
