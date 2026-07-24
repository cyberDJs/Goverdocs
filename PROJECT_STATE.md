---
id: PROJECT-STATE-GOVERDOCS
type: project-state
title: GOVERDOCS Project State
status: active
owner: GOVERDOCS
created: 2026-07-19
updated: 2026-07-24
version: 1.0.0
canonical: true
managed_by: agent
write_policy: automatic
supersedes: null
superseded_by: null
related:
  - EPIC-0001
  - ARCH-0001
  - ADR-0002
source_refs:
  - SESSION-2026-07-19-01
  - SESSION-2026-07-23-01
  - SESSION-2026-07-23-02
  - SESSION-2026-07-24-01
last_verified: 2026-07-24
review_due: null
---

# GOVERDOCS Project State

## Current state

- Version: `0.1.0`
- Phase: Release candidate hardening
- Deterministic classification and planning: implemented
- Metadata, relationship and local-link validation: implemented
- Audit receipts: implemented
- Normative technical constitution: integrated and checksum-locked
- Licence: Apache-2.0, recorded by ADR-0002 and declared through PEP 639 metadata
- Source CI: Python 3.11, 3.12 and 3.13 matrix
- Distribution CI: repeated sdist/wheel build, raw sdist payload comparison, canonical archive metadata normalization, byte-for-byte artifact comparison, strict metadata check, clean-install smoke test and runtime dependency audit
- Generated governance artifacts: deterministic and independent of wall-clock execution time
- AI writer: not implemented
- Canonical automatic write: disabled

## Exit criteria

- Ruff and mypy pass,
- the complete pytest suite passes,
- documentation health passes with 0 issues,
- sdist and wheel are built from the tagged commit,
- package metadata, embedded licence and runtime dependency closure are verified,
- a clean installation passes `pip check` and the GOVERDOCS health command,
- local and remote target refs are synchronized before tag creation,
- no autonomous `apply` command exists.
