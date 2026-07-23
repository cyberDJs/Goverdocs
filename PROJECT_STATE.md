---
id: PROJECT-STATE-GOVERDOCS
type: project-state
title: GOVERDOCS Project State
status: active
owner: GOVERDOCS
created: 2026-07-19
updated: 2026-07-23
version: 1.0.0
canonical: true
managed_by: agent
write_policy: automatic
supersedes: null
superseded_by: null
related:
  - EPIC-0001
  - ARCH-0001
source_refs:
  - SESSION-2026-07-19-01
  - SESSION-2026-07-23-01
last_verified: 2026-07-23
review_due: null
---

# GOVERDOCS Project State

## Current state

- Version: `0.1.0`
- Phase: Foundation
- Deterministic classification and planning: implemented
- Metadata, relationship and local-link validation: implemented
- Audit receipts: implemented
- Normative technical constitution: integrated and checksum-locked
- AI writer: not implemented
- Canonical automatic write: disabled

## Exit criteria

- Ruff and mypy pass,
- 10 tests pass,
- documentation health passes with 0 issues,
- installer verifies the distribution checksum,
- no autonomous `apply` command exists.
