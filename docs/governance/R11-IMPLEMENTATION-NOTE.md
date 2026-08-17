---
id: GOV-0007
type: governance
title: R11 Implementation Note
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
  - GOV-0006
source_refs:
  - GH-ISSUE-35
last_verified: null
review_due: null
---

# R11 — Implementation Note

The R11 implementation intentionally composes with, rather than replaces, R10 approval verification.

Only approval records already assessed as `VERIFIED` by the existing governance gate may enter the R11 authority calculation. This preserves exact PR, HEAD, change-digest, verifier-trust, freshness, and revocation semantics.

The authority-aware GitHub runner performs a second PR subject read before required-check publication and aborts without publishing if either HEAD or base changed during evaluation.
