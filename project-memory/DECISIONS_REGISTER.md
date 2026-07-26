---
id: DEC-REG-GOVERDOCS
type: decision-register
title: Decisions Register
status: active
owner: GOVERDOCS
created: 2026-07-19
updated: 2026-07-26
version: 1.2.0
canonical: true
managed_by: mixed
write_policy: append-only
supersedes: null
superseded_by: null
related:
  - ADR-0001
  - ADR-0002
  - ADR-0003
  - ADR-0004
source_refs:
  - SESSION-2026-07-19-01
  - SESSION-2026-07-23-02
  - SESSION-2026-07-24-02
  - SESSION-2026-07-26-01
  - SESSION-2026-07-26-02
last_verified: 2026-07-26
review_due: null
---

# Decisions Register

| ADR | Status | Decision |
|---|---|---|
| `ADR-0001` | accepted | Deterministic governor precedes AI writer and autonomous executor. |

## ADR-0002 — Adopt Apache License 2.0

- Status: accepted
- Date: 2026-07-23
- Decision: GOVERDOCS is licensed under Apache License 2.0 (`Apache-2.0`).
- Evidence: `LICENSE`, `manifests/GOVERNANCE_ARTIFACTS.yaml`
- Record: `docs/decisions/governance/ADR-0002-apache-2-license.md`


## ADR-0003 — Adopt the Initial Open-Source Governance Toolchain

- Status: accepted
- Date: 2026-07-24
- Decision: adopt pinned MkDocs Material, a MADR-inspired GOVERDOCS template, REUSE compliance and OpenSSF Scorecard as bounded presentation and evidence tools.
- Boundary: no new runtime dependencies, no automatic documentation deployment and no canonical-write authority for external tools.
- Record: `docs/decisions/governance/ADR-0003-open-source-governance-toolchain.md`


## ADR-0004 — Establish a Constitutional Framework with Scoped Operating Modes

- Status: accepted
- Date: 2026-07-26
- Decision: adopt a subordinate coordinating framework, a product operating mode and one schema-validated warn-only 10-of-10 gate while preserving the exact WORLD bytes.
- Evidence: exact implementation SHA `6236a8cae777063811b41ae00fb36f819f8468e7`, quality run `30191576044`, OpenSSF Scorecard run `30191576042` and retained artifact digests in REV-0003.
- Boundary: no autonomous canonical write, hard enforcement, tag, release or deployment.
- Record: `docs/decisions/governance/ADR-0004-constitutional-framework.md`
