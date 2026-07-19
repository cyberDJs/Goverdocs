---
id: GOV-0001
type: governance
title: Documentation Automation Governance
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
  - ADR-0001
  - ARCH-0001
  - SEC-0001
source_refs:
  - EPIC-0001
last_verified: 2026-07-19
review_due: null
---

# Documentation Automation Governance

## Authority model

1. The project filesystem is canonical.
2. Chat, ZIP and exports are snapshots, not authority.
3. Deterministic policy decides permitted operations.
4. An LLM may draft text but cannot approve its own canonical write.
5. Accepted decisions are superseded, never silently rewritten.
6. Validation failure blocks canonical writes.

## Write classes

- `automatic`: structured mutable project state.
- `append-only`: chronological register; corrections require a new entry.
- `approval-required`: a draft may be generated; canonical write requires an owner.
- `immutable`: accepted evidence cannot be modified.
- `generated`: derived output rebuilt from canonical sources.
