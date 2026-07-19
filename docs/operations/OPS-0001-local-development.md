---
id: OPS-0001
type: operations
title: Local Development Runbook
status: active
owner: GOVERDOCS
created: 2026-07-19
updated: 2026-07-19
version: 1.0.0
canonical: true
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - WB-0001
  - ARCH-0001
source_refs:
  - SESSION-2026-07-19-01
last_verified: 2026-07-19
review_due: null
---

# Local Development Runbook

## Bootstrap

Run `./scripts/bootstrap_local.sh`.

## Verification

Run `./scripts/verify.sh`.

## Recovery

Remove `.venv` and rerun bootstrap. Generated manifests can be rebuilt using `goverdocs rebuild-index --root .`.
