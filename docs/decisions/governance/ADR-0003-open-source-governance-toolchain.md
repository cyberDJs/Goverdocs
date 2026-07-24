---
id: ADR-0003
type: architecture-decision
title: Adopt the Initial Open-Source Governance Toolchain
status: accepted
owner: GOVERDOCS
created: 2026-07-24
updated: 2026-07-24
version: 1.0.0
canonical: true
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - EPIC-0001
  - WB-0002
  - PROJECT-STATE-GOVERDOCS
  - REV-0002
source_refs:
  - SESSION-2026-07-24-02
last_verified: 2026-07-24
review_due: 2026-10-01
---

# ADR-0003: Adopt the Initial Open-Source Governance Toolchain

## Context and problem

GOVERDOCS must become a practical engineering source of truth without
reimplementing mature documentation, licence-compliance and repository-security
tooling. The integration must preserve GOVERDOCS as the canonical governance
authority, avoid new runtime dependencies and remain small, reversible and
audit-friendly.

## Decision drivers

- reuse mature open-source capabilities instead of duplicating them,
- keep canonical rules, metadata and relationships in Git,
- pin every executable dependency and GitHub Action,
- separate presentation and evidence production from canonical mutation,
- avoid automatic documentation deployment in the first integration,
- preserve the current Python runtime dependency closure,
- record third-party licences and review boundaries.

## Considered options

### Build all capabilities inside GOVERDOCS

Rejected because it would duplicate mature tooling, increase maintenance cost
and delay governance features that are unique to GOVERDOCS.

### Adopt a large developer portal or compliance platform immediately

Backstage, OSS Review Toolkit, OPA bundles and formal attestation systems remain
valid future integrations. They are deferred because the current repository
needs a smaller proof of integration before adding services, containers or a
second policy language.

### Adopt a minimal composable toolchain

Selected. Each tool has one bounded responsibility and can be removed without
changing the GOVERDOCS metadata model or canonical documents.

## Decision

Adopt the following initial toolchain:

- MkDocs `1.6.1` plus Material for MkDocs `9.7.7` for a strict, build-only
  documentation portal,
- a GOVERDOCS-specific ADR template inspired by MADR, without a MADR runtime
  dependency or verbatim template import,
- REUSE tool `6.2.0` and REUSE Specification 3.3 metadata for repository-wide
  SPDX licence compliance,
- OpenSSF Scorecard Action `v2.4.3`, pinned to full commit SHA, in a separate
  restricted workflow that produces SARIF evidence.

The `docs` and `compliance` Python extras are development and CI tooling only.
They must not become base runtime dependencies of the published GOVERDOCS
wheel. The documentation portal must be built with `--strict`; automatic Pages
or production deployment remains disabled.

## Consequences

### Positive

- GOVERDOCS gains a navigable documentation build without building a custom UI.
- Licence metadata becomes machine-verifiable for every tracked file.
- Repository security findings become reviewable in GitHub code scanning.
- ADR authors receive a consistent evidence-oriented template.
- Tool versions, licences and trust boundaries are explicit and testable.

### Negative and accepted trade-offs

- CI installs additional development-only packages.
- The REUSE tool has mixed upstream licensing and GPL-licensed tool code; it is
  therefore isolated from the runtime dependency set.
- Material for MkDocs requires a documented reassessment before its current
  maintenance window ends.
- The portal duplicates selected explanatory text, so it must clearly point to
  canonical source documents and remain non-normative.

## Verification and required evidence

- `mkdocs build --strict` completes without warnings,
- `reuse lint` reports compliance,
- all GitHub Action references use full 40-character commit SHAs,
- the base wheel runtime dependencies remain only PyYAML and jsonschema,
- regression tests verify pins, workflow permissions, licence copies and the
  presentation/canonical boundary,
- generated governance registry, relationship graph, status summary and index
  include ADR-0003 and WB-0002.

## Security and trust boundaries

- Scorecard receives only the permissions required by its official workflow.
- Checkout credentials are not persisted in the Scorecard job.
- Documentation build output is an artifact, not a canonical input.
- External tools may report evidence but may not approve or write canonical
  governance content.

## Migration and rollback

The integration is additive. Rollback removes the new optional dependencies,
workflows, portal sources, REUSE metadata, templates and related documentation,
then regenerates the governance index and manifests. Runtime package behaviour
and the canonical technical constitution are unchanged.

## Approval

The project owner explicitly authorized implementation of the proposed initial
open-source toolchain on 2026-07-24. Commit, push, tag, publication and release
remain separate approval-gated operations.
