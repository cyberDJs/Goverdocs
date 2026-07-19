---
id: ADR-0001
type: architecture-decision
title: Deterministic Governor Before AI Writer
status: accepted
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
  - ARCH-0001
  - GOV-0001
  - EPIC-0001
source_refs:
  - SESSION-2026-07-19-01
last_verified: 2026-07-19
review_due: null
---

# Deterministic Governor Before AI Writer

## Context

Autonomous documentation writers can create plausible but false project history.

## Decision

Build deterministic classification, policy, validation and approval controls before adding an LLM writer or execution runtime.

## Consequences

- V0.1 has no `apply` command.
- AI integration remains an adapter, not governance authority.
- Future canonical writes require policy validation and receipts.
