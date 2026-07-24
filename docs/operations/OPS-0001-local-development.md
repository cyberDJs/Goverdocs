---
id: OPS-0001
type: operations
title: Local Development Runbook
status: active
owner: GOVERDOCS
created: 2026-07-19
updated: 2026-07-24
version: 1.0.0
canonical: true
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - WB-0001
  - WB-0002
  - ADR-0003
  - ARCH-0001
source_refs:
  - SESSION-2026-07-19-01
  - SESSION-2026-07-24-02
last_verified: 2026-07-24
review_due: null
---

# Local Development Runbook

## Bootstrap

Run `./scripts/bootstrap_local.sh`.

## Verification

Run `./scripts/verify.sh`.

## Documentation and compliance tooling

Install the optional, exactly pinned tools:

```bash
.venv/bin/python -m pip install -e '.[docs,compliance]'
```

Run the local gates:

```bash
.venv/bin/mkdocs build --strict
.venv/bin/reuse lint
```

The MkDocs output directory `site/` is ignored and must not be treated as a
canonical source. This runbook does not authorize automatic deployment.

## Recovery

Remove `.venv` and rerun bootstrap. Generated manifests can be rebuilt using
`goverdocs rebuild-index --root .`. Remove `site/` if a clean local
presentation build is required.
