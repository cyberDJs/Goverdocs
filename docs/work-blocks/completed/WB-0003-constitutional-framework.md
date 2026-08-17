---
id: WB-0003
type: work-block
title: Establish the Constitutional Framework
status: completed
owner: GOVERDOCS
created: 2026-07-26
updated: 2026-08-17
version: 1.0.1
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
  - SESSION-2026-07-26-02
  - GITHUB-MAIN-b002135d4ce532c451bf6eee9cd9c8782431ee92
  - GITHUB-RELEASE-v0.1.0@018d8b7d5f5ab12f537991fe565b9dae4af3b0d9
last_verified: 2026-08-17
review_due: 2026-09-17
---

# WB-0003: Establish the Constitutional Framework

## Goal

Establish and verify a reversible, warn-only constitutional framework without
modifying the canonical WORLD bytes or creating tag, release or deployment
side effects.

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
- 40 pytest tests PASS,
- GOVERDOCS validation PASS,
- health PASS with 24 documents and 0 issues,
- strict MkDocs build PASS,
- REUSE 3.3 PASS for 108 of 108 files,
- verified 26-path scope,
- separately approved commit and push of `6236a8cae777063811b41ae00fb36f819f8468e7`,
- no tag, release or deployment.

The earlier V1 Ruff failure also demonstrated automatic rollback to the exact
clean base. Human review identified bounded contract-hardening corrections that
must pass the same gates before acceptance.

## Rollback

Reverse the patch, regenerate derived artefacts and rerun validation. After a
commit use a normal revert; never rewrite shared history.

## Remote verification and closure

- quality run `30191576044`: `success`,
- OpenSSF Scorecard run `30191576042`: `success`,
- package artifact `8628731800`: `sha256:dcbcb253584d86bedc53f145f5461bb1283a6382b0f405cc5cc853cf9b4ce2ab`,
- documentation artifact `8628731425`: `sha256:0ec8927f162e5191727833d5df8daeb0113c577f8e24a50a1dd1b78209429874`,
- SARIF artifact `8628727141`: `sha256:ea7a2f955989d7c6ce2df137c8a18e0cf311ef717740d180507a7e0ea7ebac93`,
- REV-0003: accepted for the declared warn-only scope.

WB-0003 is completed. Tag, release, deployment, adoption and product-impact
verification remain outside this work block.

## Revalidation — 2026-08-17

WB-0003 remains correctly `completed`; no reopening or supersession is needed.
Its original goal, non-goals and exact verification evidence remain historical
facts for the bounded 2026-07-26 work block.

Current GitHub revalidation was performed against
`main@b002135d4ce532c451bf6eee9cd9c8782431ee92`. A later separately governed
release `v0.1.0` exists at
`018d8b7d5f5ab12f537991fe565b9dae4af3b0d9`. Because release creation was a
non-goal of WB-0003, that later release does not change this work block's
completion semantics.

No current local Git state is asserted by this revalidation. Next review is due
`2026-09-17`.
