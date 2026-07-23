---
id: ADR-0002
type: architecture-decision
title: Adopt Apache License 2.0
status: accepted
owner: GOVERDOCS
created: 2026-07-23
updated: 2026-07-23
version: 1.0.0
canonical: true
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - GOV-0001
  - PROJECT-STATE-GOVERDOCS
  - OQ-GOVERDOCS
source_refs:
  - SESSION-2026-07-23-02
last_verified: 2026-07-23
review_due: null
---

# ADR-0002: Adopt Apache License 2.0

## Status

Accepted.

## Context

GOVERDOCS requires an explicit licence before its first public source publication.
The project is intended to be reusable as a governance kernel, CLI and Python
package without making an AI provider or hosted service mandatory.

The evaluated options were:

- Apache License 2.0,
- GNU Affero General Public License 3.0,
- proprietary distribution.

## Decision

GOVERDOCS is licensed under the Apache License, Version 2.0, identified by the
SPDX expression `Apache-2.0`.

The canonical licence text is stored in the repository root as `LICENSE`.

## Consequences

- The project may be used, modified and redistributed under Apache-2.0 terms.
- Redistributions must preserve the required licence and attribution notices.
- The Apache-2.0 patent provisions apply.
- A future licence change requires a separate governance and legal review.
- Dependency licences remain subject to a separate supply-chain audit.

## Controls

- `LICENSE` is checksum-locked in `manifests/GOVERNANCE_ARTIFACTS.yaml`.
- `tests/test_license.py` verifies its canonical SHA-256.
- The decision is recorded in the append-only decision and session registers.

## Non-goals

This decision does not:

- perform a dependency licence audit,
- create a contributor licence agreement,
- create a `NOTICE` file,
- publish, tag or release the repository,
- change package metadata or public APIs.

## Rollback

Before public distribution, revert the implementing Git commit and repeat the
licence decision workflow. Do not rewrite Git history.
