---
id: WB-0002
type: work-block
title: Integrate the Initial Open-Source Governance Toolchain
status: active
owner: GOVERDOCS
created: 2026-07-24
updated: 2026-07-24
version: 1.0.0
canonical: true
managed_by: mixed
write_policy: automatic
supersedes: null
superseded_by: null
related:
  - EPIC-0001
  - ADR-0003
  - PROJECT-STATE-GOVERDOCS
  - REV-0002
source_refs:
  - SESSION-2026-07-24-02
last_verified: 2026-07-24
review_due: null
---

# WB-0002: Integrate the Initial Open-Source Governance Toolchain

## Goal

Add a small, pinned and reversible open-source toolchain that improves
presentation, ADR authoring, licence compliance and repository security without
changing GOVERDOCS runtime behaviour or canonical-write boundaries.

## Scope

- strict MkDocs Material portal build,
- GOVERDOCS-specific MADR-compatible ADR template,
- REUSE metadata, canonical SPDX licence copy and CI lint,
- SHA-pinned OpenSSF Scorecard workflow with SARIF output,
- third-party version and licence record,
- regression tests and governance evidence updates.

## Out of scope

- automatic GitHub Pages deployment,
- Backstage, OPA, ORT, SLSA or in-toto integration,
- AI writer or autonomous canonical write,
- tag, release or package publication,
- changes to the canonical technical constitution.

## Acceptance criteria

- all existing Ruff, mypy, pytest, validation and health gates pass,
- `mkdocs build --strict` passes,
- `reuse lint` passes,
- Scorecard workflow permissions and action pins pass regression tests,
- documentation artifacts build without modifying tracked files,
- generated governance artifacts are deterministic and current,
- Git diff is restricted to the reviewed integration scope.

## Rollback

Restore the modified files, remove the exact new integration paths, regenerate
the governance index and manifests, and rerun the complete source and
governance gates. Do not rewrite Git history or use force push.
