---
id: GOV-0006
type: governance
title: R11 Authority Enrollment State
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
source_refs:
  - GH-ISSUE-35
last_verified: null
review_due: null
---

# R11 — Authority Enrollment State

Current live repository enrollment contains only the `nulleimy` GitHub identity. That identity is bound as `project-owner` in the canonical governance workflow.

No `independent-reviewer` identity is currently bound. Consequently:

- critical changes cannot satisfy the R11 two-actor quorum;
- the PR author cannot substitute for the missing independent actor;
- no synthetic identity or role alias may satisfy the missing capability;
- R11 full positive verification remains enrollment-blocked until a real second GitHub identity is enrolled and explicitly bound.

This document records the external enrollment boundary; it does not weaken or modify the R9 ruleset.
