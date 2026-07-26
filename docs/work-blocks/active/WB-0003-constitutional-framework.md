---
id: WB-0003
type: work-block
title: Establish the Constitutional Framework
status: active
owner: GOVERDOCS
created: 2026-07-26
updated: 2026-07-26
version: 0.1.1
canonical: true
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - CONST-FRAMEWORK-GOVERDOCS
  - PRODUCT-MODE-GOVERDOCS
  - ADR-0004
  - REV-0003
  - PROJECT-STATE-GOVERDOCS
source_refs:
  - SESSION-2026-07-26-01
last_verified: null
review_due: 2026-08-15
---

# WB-0003: Establish the Constitutional Framework

## Goal

Prepare and locally verify a reversible, warn-only constitutional framework
without modifying the canonical WORLD bytes or creating commit, push, tag or
release side effects.

## Scope

- coordinating framework,
- product/decision/execution operating mode,
- machine-readable 10-of-10 gate and schema,
- optional configuration and validator integration,
- ADR, review, tests and generated registry updates.

## Non-goals

- replacing or editing WORLD,
- autonomous canonical writes,
- runtime deployment,
- hard enforcement of change scoring,
- tag or release creation.

## Acceptance criteria

- WORLD checksum remains exact,
- gate schema and contract tests pass,
- project validation and health pass,
- full pytest, Ruff and mypy pass,
- generated artefacts are deterministic,
- strict docs and REUSE checks pass,
- diff remains bounded and rollback is demonstrated.

## Local verification evidence

V1.0.1 was applied to the exact clean base
`e84e982c59e4c2001bc4b720456046f2447d4f70` and produced:

- unchanged WORLD SHA-256,
- deterministic rebuild idempotence PASS,
- Ruff PASS,
- mypy PASS for 14 source files,
- 39 pytest tests PASS,
- GOVERDOCS validation PASS,
- health PASS with 24 documents and 0 issues,
- strict MkDocs build PASS,
- REUSE 3.3 PASS for 108 of 108 files,
- verified 26-path scope,
- no commit, push, tag or release.

The earlier V1 Ruff failure also demonstrated automatic rollback to the exact
clean base. Human review identified bounded contract-hardening corrections that
must pass the same gates before acceptance.

## Rollback

Reverse the patch, regenerate derived artefacts and rerun validation. After a
commit use a normal revert; never rewrite shared history.
