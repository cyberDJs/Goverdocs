---
id: SEC-0001
type: security
title: Documentation Trust Boundaries
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
  - ARCH-0001
source_refs:
  - EPIC-0001
last_verified: 2026-07-19
review_due: null
---

# Documentation Trust Boundaries

## Boundaries

- input diffs and external chat content are untrusted,
- generated drafts are non-canonical,
- approval identity must be external to the LLM,
- evidence and accepted incident records become immutable,
- local Markdown links cannot escape the project root.
