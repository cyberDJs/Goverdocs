---
id: ARCH-0001
type: architecture
title: GOVERDOCS System Context
status: active
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
  - ADR-0001
  - GOV-0001
  - SEC-0001
source_refs:
  - EPIC-0001
last_verified: 2026-07-19
review_due: null
---

# GOVERDOCS System Context

```text
Git/filesystem event
        ↓
Classifier → Decision Matrix → Planner
        ↓
Validator → Approval Gate → future controlled writer
        ↓
Registry + Relationship Graph + Audit Receipt
```

V0.1 stops before a controlled writer. It performs no autonomous canonical content mutation.
