---
id: WB-0004
type: work-block
title: Freeze Product Baseline and Derive Governance Gate R1
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
  - ARCH-0002
  - ADR-0005
  - ARCH-0001
  - PRODUCT-MODE-GOVERDOCS
  - PROJECT-STATE-GOVERDOCS
source_refs:
  - ARCH-0002
  - ADR-0005
last_verified: null
review_due: 2026-09-17
---

# WB-0004: Freeze Product Baseline and Derive Governance Gate R1

## Goal

Create one bounded product architecture baseline for GOVERDOCS and derive the
smallest implementation slice that tests the core product hypothesis without
introducing autonomous writes, a hosted control plane or unnecessary
infrastructure.

## Scope

- define the canonical product category and value proposition,
- define ICP/JTBD and explicit non-ICP,
- define competitive and integration boundaries,
- define target architecture and stable domain concepts,
- define evidence/approval and commercial boundaries,
- define sequenced roadmap and product metrics,
- define Governance Gate R1 as the first implementation slice.

## Non-goals

- implementing Governance Gate R1 in this documentation branch,
- AI-generated canonical documentation,
- merge enforcement by GOVERDOCS itself,
- SaaS backend, database or web dashboard,
- fixed pricing,
- compliance certification claims,
- tag, release or deployment.

## First implementation PR derived from this work block

Proposed branch:

`feat/governance-gate-r1`

Proposed minimal flow:

```text
ChangeSet
→ existing classifier
→ existing decision matrix / planner
→ obligations and evidence gaps
→ existing validator signals
→ GateReport
```

### Required `GateReport` behavior

- deterministic for the same input and policy version,
- one top-level result: `PASS`, `WARN` or `BLOCKED`,
- explicit evaluated scope and input identity,
- applied policy/version references,
- classified governance events,
- obligations with rationale and severity,
- missing/stale evidence or approval requirements,
- machine-readable JSON output,
- concise human-readable CLI output,
- no repository mutation.

### Required tests

- same inputs produce byte-stable canonical JSON representation,
- a missing blocking obligation produces `BLOCKED`,
- a non-blocking freshness finding produces `WARN`,
- a satisfied bounded fixture produces `PASS`,
- malformed or ambiguous critical input fails closed,
- the evaluation path does not write governed files,
- existing classifier/planner/validator tests remain green.

## Acceptance criteria for this documentation slice

- `ARCH-0002` contains all eight required product-baseline dimensions without
creating parallel canonical sources,
- `ADR-0005` records the category/architecture choice and rejected alternatives,
- this work block defines a bounded first implementation PR,
- all new relationships resolve,
- repository validation and health pass,
- full quality CI succeeds on the exact branch head,
- no merge, tag, release or deployment is performed by this work block.

## Product validation criteria after implementation

Governance Gate R1 is not product-success evidence by itself. Dogfood and
external pilots must measure at least:

- false-positive rate,
- false-negative rate,
- time to governed decision,
- governance drift detected,
- remediation lead time,
- developer friction,
- audit preparation effort.

Commercial expansion remains `UNKNOWN` until real users demonstrate recurring
value and willingness to pay.

## Rollback

Drop the proposal branch before merge or revert the eventual documentation
commit after a separately approved merge. Governance Gate R1 must be developed
on a separate branch and remain independently revertible.
