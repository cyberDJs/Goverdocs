---
id: CTX-GOVERDOCS
type: current-context
title: Current Context
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
  - PROJECT-STATE-GOVERDOCS
  - WB-0001
  - ADR-0002
  - ADR-0003
  - WB-0002
  - REV-0002
source_refs:
  - SESSION-2026-07-19-01
  - SESSION-2026-07-23-01
  - SESSION-2026-07-23-02
  - SESSION-2026-07-24-01
  - SESSION-2026-07-24-02
last_verified: 2026-07-24
review_due: null
---

# Current Context

GOVERDOCS V0.1 is a deterministic documentation governor. The canonical technical constitution is integrated as an immutable, checksum-locked governance artifact. Validation hardening precedes any draft writer or controlled apply workflow.

The project licence is Apache-2.0. The public `main` branch exists and tracks `origin/main`. A release tag may be created only from a clean target commit whose local and remote refs are identical and whose source and distribution CI gates have completed successfully.

The current release-hardening scope standardizes Python package licence metadata, removes an unnecessary runtime dependency extra, makes generated governance metadata source-derived, and canonicalizes sdist archive metadata before byte-for-byte distribution verification. Tag creation and GitHub release publication remain separate approval-gated operations.

The first open-source governance toolchain integration adds a build-only MkDocs
Material portal, a GOVERDOCS-specific MADR-compatible ADR template, REUSE
licence compliance and a separate OpenSSF Scorecard workflow. These tools are
presentation and evidence producers; canonical governance authority remains in
GOVERDOCS documents, policies, schemas and Git history. Documentation
publication, automatic canonical writes, tags and releases remain disabled.
