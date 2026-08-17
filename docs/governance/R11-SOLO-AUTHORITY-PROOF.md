---
id: GOV-0009
type: governance
title: R11 Solo Authority Fail-Closed Proof
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
  - GOV-0005
  - GOV-0008
source_refs:
  - GH-ISSUE-35
last_verified: null
review_due: null
---

# R11 — Solo Authority Fail-Closed Proof

This document exists only to create a minimal live `governance_change` / critical obligation for R11 verification.

The proof is successful only if a valid exact-head `project-owner` approval from the PR author is insufficient to satisfy R11 authority, the required `GOVERDOCS Governance Gate` remains `BLOCKED`, and GitHub rejects merge server-side.

No second actor is fabricated. A positive two-actor proof remains enrollment-blocked until a real independent GitHub identity is enrolled and role-bound.
