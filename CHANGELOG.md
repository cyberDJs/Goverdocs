# Changelog

## Unreleased

No unreleased changes.

## 0.1.0 — 2026-07-24

- established the deterministic documentation governance kernel,
- added 45 documentation events, CLI planning, validation, registries, relationship graph and audit receipts,
- integrated the canonical technical constitution as an immutable checksum-locked artifact,
- selected Apache License 2.0 and recorded the decision in ADR-0002,
- added PEP 639 package licence metadata and a reproducible pinned setuptools backend,
- canonicalized sdist archive metadata so repeated release builds produce byte-for-byte identical source archives,
- removed the unnecessary `jsonschema[format]` runtime extra and its `rfc3987` transitive dependency,
- made `rebuild-index` outputs deterministic by deriving generated timestamps from governed document metadata,
- added regression coverage for CLI orchestration, licence integrity, package metadata and release gates,
- added CI matrix verification plus sdist/wheel build, strict metadata checking, clean-install smoke testing, runtime dependency auditing and artifact retention.
