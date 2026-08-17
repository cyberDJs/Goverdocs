---
id: GOV-0005
type: governance
title: R10 Approval Revocation Probe
status: proposed
owner: GOVERDOCS
created: 2026-08-17
updated: 2026-08-17
version: 1.0.0
canonical: false
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - GOV-0004
source_refs:
  - GH-ISSUE-27
last_verified: 2026-08-17
review_due: null
---

# R10 — Approval Revocation Probe

## Purpose

Disposable governed carrier for the live R10.4 exact-head approval revocation proof.

The same exact head must move from BLOCKED to PASS after `decision=approved`, then return to BLOCKED after a later exact-subject `decision=revoked` marker from the same project-owner actor.

This document is not intended to become canonical and the proof PR will be closed unmerged.
