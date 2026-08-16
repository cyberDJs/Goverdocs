---
id: ADR-0005
type: architecture-decision
title: Position GOVERDOCS as an Evidence-Driven Change Governance Control Plane
status: proposed
owner: GOVERDOCS
created: 2026-08-17
updated: 2026-08-17
version: 1.0.0
canonical: true
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - ARCH-0001
  - ARCH-0002
  - ADR-0001
  - ADR-0004
  - CONST-FRAMEWORK-GOVERDOCS
  - PRODUCT-MODE-GOVERDOCS
source_refs:
  - ARCH-0002
  - PRODUCT-MODE-GOVERDOCS
last_verified: null
review_due: 2026-09-17
---

# ADR-0005: Position GOVERDOCS as an Evidence-Driven Change Governance Control Plane

## Context and problem

The existing GOVERDOCS kernel already provides deterministic classification,
planning, validation, registry/evidence concepts and explicit approval boundaries.
The product category, however, could drift into several already-crowded markets:
AI documentation generation, documentation hosting, developer portals, general
policy engines or autonomous software agents.

Those directions would increase product surface and operational complexity while
duplicating capabilities that mature external tools and standards already provide.
The stronger unresolved problem is the gap between a software change and a
trustworthy answer to what that change requires, what evidence is missing, who
must approve it and whether it may advance.

## Decision

Position and evolve GOVERDOCS as a **repo-native, evidence-driven software change
governance control plane**.

The deterministic kernel remains authoritative for semantic classification,
policy evaluation, obligations and gate status. External systems remain
responsible for their native authority boundaries:

- SCM platforms enforce merge permissions and branch/ruleset policy,
- CI systems execute jobs,
- provenance/signing standards provide cryptographic attestations,
- documentation platforms render and host documentation,
- AI systems may assist with bounded drafting and explanation.

GOVERDOCS coordinates these signals and produces an explainable evidence-bound
governance result. It does not replace them.

The first product implementation derived from this decision is a read-only
Governance Gate R1 that composes existing classifier, decision matrix, planner
and validator capabilities into a deterministic `GateReport` with
`PASS`, `WARN` or `BLOCKED` status.

## Decision drivers

- preserve the existing deterministic-governor architecture,
- maximize differentiation while minimizing duplicated infrastructure,
- make evidence and approval binding first-class product concepts,
- keep the open-source kernel useful without hosted services,
- integrate with established standards instead of inventing replacements,
- make AI assistance bounded and subordinate to deterministic rules and human
authority,
- validate the core product hypothesis before SaaS or enterprise expansion.

## Considered options

### 1. AI documentation generator

Rejected as the primary category. Draft generation can be a later bounded
capability, but it does not justify the governance kernel and competes directly
with mature documentation products.

### 2. Developer portal / engineering catalog

Rejected. It would require a broad UI, integration and service-catalog surface
unrelated to the strongest GOVERDOCS capability. Existing portals can consume
GOVERDOCS results through adapters.

### 3. General policy-as-code platform

Rejected. GOVERDOCS needs a bounded policy contract for software-change
governance, not a new universal policy language.

### 4. Autonomous governance agent

Rejected. Generative systems must not approve their own output or silently
change canonical policy/enforcement state.

### 5. Evidence-driven change governance control plane

Selected. It directly extends the current deterministic architecture and creates
an integration layer between change semantics, obligations, evidence, approvals
and enforcement systems.

## Consequences

Positive:

- product identity becomes narrow and defensible,
- the existing kernel becomes product infrastructure rather than prototype code,
- open-core and enterprise boundaries become clearer,
- AI can be added without becoming the authority model,
- SaaS can be deferred until multi-repository coordination is validated,
- standards such as SCM rules, attestations and external policy engines can be
integrated instead of reimplemented.

Negative:

- success depends on low false-positive/false-negative rates,
- evidence semantics and approval freshness require careful contract design,
- the product must prove developer value rather than merely add governance steps,
- commercial willingness-to-pay remains unverified until external pilots.

## Constraints

This decision does not authorize:

- an autonomous canonical writer,
- hard merge enforcement by GOVERDOCS itself,
- a hosted control plane,
- a graph database,
- a new cryptographic identity/signing system,
- fixed commercial pricing,
- compliance certification claims,
- release or deployment.

## Verification required before acceptance

- `ARCH-0002` passes metadata, relationship and documentation validation,
- the proposed architecture does not conflict with WORLD, the constitutional
framework or the product operating mode,
- the first implementation slice has bounded acceptance criteria and rollback,
- repository CI passes for the exact proposal SHA,
- acceptance is recorded separately from implementation and merge authorization.

## Rollback / supersession

Before acceptance, drop the proposal branch. After acceptance, supersede this ADR
with a new decision rather than silently rewriting the historical decision.

## Approval

`PROPOSED`. Creation of this ADR records the selected design proposal only.
It does not prove product-market fit, external adoption, monetization or
implementation of Governance Gate R1.
