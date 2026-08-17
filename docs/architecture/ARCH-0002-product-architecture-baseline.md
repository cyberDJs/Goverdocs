---
id: ARCH-0002
type: architecture
title: GOVERDOCS Product Architecture Baseline
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
  - ADR-0001
  - ADR-0004
  - CONST-FRAMEWORK-GOVERDOCS
  - PRODUCT-MODE-GOVERDOCS
source_refs:
  - PRODUCT-MODE-GOVERDOCS
  - CONST-FRAMEWORK-GOVERDOCS
last_verified: null
review_due: 2026-09-17
---

# GOVERDOCS Product Architecture Baseline

## 0. Normative scope

This document is the single proposed canonical product baseline for GOVERDOCS.
It consolidates product vision, ICP/JTBD, positioning, target architecture,
domain model, evidence model, commercial model and roadmap so that these rules
do not drift across parallel documents.

It does not change the authority of `WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md`,
`GOVERDOCS_CONSTITUTIONAL_FRAMEWORK.md` or
`PRODUCT_DECISION_EXECUTION_OPERATING_MODE.md`. Conflicts are `BLOCKED`.

Acceptance of this baseline does not authorize merge, release, deployment,
autonomous canonical writes, paid service operation or enterprise compliance
claims.

## 1. PRODUCT_VISION

### Category

GOVERDOCS is a **repo-native, evidence-driven software change governance control
plane**.

It exists to answer five questions for a material software change:

1. What changed semantically?
2. What governance obligations does that change create?
3. What evidence is required and what evidence is missing?
4. Who or what authority must approve the transition?
5. Is the change safe to advance for the declared scope?

### Product promise

> From software change to verified evidence.

GOVERDOCS determines what a software change requires, why it requires it, what
evidence is missing, who must approve it and whether it may safely advance.

### North-star workflow

```text
Git diff / PR / repository state
            ↓
         ChangeSet
            ↓
 semantic classification
            ↓
 versioned policy evaluation
            ↓
       Obligations
            ↓
 evidence + approval requirements
            ↓
 deterministic validation
            ↓
     PASS / WARN / BLOCKED
            ↓
 exact-state receipt
```

The first stable product remains read-only with respect to canonical content.
Controlled writing is a later, separately authorized capability.

## 2. ICP_AND_JOBS_TO_BE_DONE

### Primary ICP

Platform Engineering, Developer Experience, Security Engineering and Engineering
Governance teams operating Git-based software delivery, initially GitHub-centric.

Initial pilot organizations should normally have:

- multiple active repositories or a repository with meaningful governance burden,
- CI/CD and code review,
- docs-as-code, ADR, policy or compliance requirements,
- increasing use of AI-assisted software changes,
- a real cost from stale governance, missing evidence or manual audit preparation.

### Primary jobs to be done

When a software change is proposed, teams need to:

- determine its governance and documentation impact without relying on memory,
- know which evidence and approvals are required before progression,
- detect stale, contradictory or missing governance state,
- bind approvals and verification to an exact change state,
- produce an audit trail without reconstructing it manually later,
- let AI assist without giving generative output decision authority.

### Explicit non-ICP for the first product

- teams seeking only a documentation website,
- teams seeking a general-purpose developer portal,
- teams seeking an autonomous coding agent,
- organizations without a concrete governance or evidence problem.

## 3. POSITIONING

GOVERDOCS must integrate with existing categories rather than replace them.

| Existing category | GOVERDOCS boundary |
|---|---|
| Documentation platforms | Do not compete on hosting/editor/search; govern change obligations and evidence. |
| Developer portals / service catalogs | Do not build a general IDP; expose governance results through adapters. |
| Policy-as-code engines | Do not invent a general policy language; keep native deterministic policy and allow adapters later. |
| GitHub rules / CODEOWNERS | Do not replace merge authorization; emit semantic gate results that GitHub can enforce. |
| SLSA / in-toto / Sigstore | Do not replace provenance/signing standards; export or bind GOVERDOCS evidence to them. |
| AI coding/documentation agents | Do not compete as an IDE; govern bounded AI-assisted changes. |

### Defensible product surface

The core differentiator is the mapping:

```text
software change
→ semantic governance event
→ obligation
→ evidence requirement
→ approval requirement
→ verification result
→ advancement decision
```

The moat is not Markdown generation. It is deterministic, explainable and
evidence-bound change governance.

## 4. TARGET_ARCHITECTURE

### Plane A — Observation

Inputs are normalized without granting authority:

- Git diff, commit and pull request metadata,
- repository files and governed document metadata,
- CI/check results,
- configured policy and decision matrix,
- later: external evidence and deployment signals through explicit adapters.

Output: `ChangeSet`.

### Plane B — Deterministic Governance Kernel

```text
ChangeSet
   ↓
Classifier
   ↓
GovernanceEvent[]
   ↓
PolicyEvaluator
   ↓
Obligation[]
   ↓
Planner / Gate evaluator
```

Existing classifier, decision matrix, planner and validator remain the
foundation. The first product slice should compose them rather than replace
them.

### Plane C — Trust and Evidence

The kernel consumes and produces explicit evidence objects. Evidence is never
inferred solely from generative text.

### Plane D — Enforcement Adapters

GOVERDOCS returns a standard semantic result:

- `PASS` — all blocking obligations for declared scope are satisfied,
- `WARN` — non-blocking gaps or review conditions exist,
- `BLOCKED` — required evidence, approval or consistency is missing.

GitHub or another SCM remains responsible for merge enforcement.

### Plane E — AI Assistance

AI may explain, summarize, detect candidate contradictions and prepare bounded
drafts. AI may not approve its own output, mark unsupported state as verified,
change enforcement policy autonomously or perform canonical writes without a
separate grant.

### Plane F — Learning Feedback

Operational feedback may generate policy-improvement proposals from false
positives, false negatives, remediation outcomes and pilot observations.
Learning output is always a proposal. A versioned deterministic policy change
requires testing and approval before enforcement.

### Plane G — Hosted Team / Enterprise Control Plane

Only after external pilot evidence justifies it:

- multi-repository evidence aggregation,
- shared policy distribution,
- organization identity/RBAC,
- retention and audit export,
- analytics for governance outcomes,
- billing and enterprise support.

The hosted plane must not be required for the open-source single-repository
kernel.

## 5. DOMAIN_MODEL

The stable domain model should converge on these concepts:

### `ChangeSet`
Exact bounded input state for evaluation: repository identity, base/head or
content digests, changed paths, relevant metadata and evaluation scope.

### `GovernanceEvent`
A semantic fact derived deterministically from a `ChangeSet`, such as an API,
security-boundary, dependency, architecture, deployment, governance or
canonical-document change.

### `Obligation`
A required action or evidence condition created by policy for a governance
event. It contains rationale, severity, source policy and satisfaction rules.

### `PolicyEvaluation`
Deterministic evaluation record showing which versioned rules were applied and
why they produced their result.

### `EvidenceItem`
A typed claim-supporting object with subject, type, source, scope, digest,
producer/verifier, timestamp/freshness, status and references.

### `ApprovalRequirement`
A declaration that a named approval authority is required for an exact scope
and state.

### `Approval`
An attributable approval bound to an exact subject and state. Approval is not
verification and becomes stale when its binding conditions no longer hold.

### `VerificationResult`
A deterministic or independently reproduced result for a declared claim and
scope.

### `Exception`
A bounded, attributable, reviewable and expiring deviation from policy.

### `Receipt`
An immutable representation of evaluation inputs, applied policy versions,
obligations, evidence references, approvals, verification results and final
status for an exact evaluated state.

The model must preserve the existing invariant:

```text
APPROVED != IMPLEMENTED
IMPLEMENTED != VERIFIED
VERIFIED != RELEASED
RELEASED != ADOPTED
```

## 6. EVIDENCE_MODEL

### Evidence chain

For each relevant transition, GOVERDOCS should be able to link:

```text
problem / change signal
→ exact change state
→ semantic classification
→ policy decision
→ obligations
→ evidence
→ approval
→ verification
→ advancement result
→ receipt
```

Later lifecycle adapters may append release, deployment, runtime, adoption and
impact evidence. They must not be fabricated when unavailable.

### Approval identity R1

The first implementable approval model should use existing SCM identity and
bind approval to:

- actor identity,
- repository,
- pull request or declared subject,
- exact head SHA/digest,
- approval type,
- timestamp,
- applicable policy requirement.

Cryptographic signing or external identity can later be added through standard
attestation/signing adapters. GOVERDOCS must not invent a new cryptographic
identity system.

### Evidence quality

Every material evidence item should expose provenance, integrity, freshness and
scope. Missing or stale blocking evidence produces `BLOCKED`; absence must never
be silently converted into success.

## 7. COMMERCIAL_MODEL

### Community / Apache-2.0 core

Free adoption surface:

- CLI,
- deterministic classifier/planner/validator,
- single-repository governance gate,
- local policies and schemas,
- local evidence and receipts,
- GitHub Action / CI usage,
- machine-readable outputs.

The core must remain useful without a hosted account.

### Team / Cloud

Paid value is operational coordination rather than locking basic validation:

- GitHub App,
- multi-repository governance view,
- central evidence inbox and retention,
- shared policy registry and distribution,
- drift/freshness monitoring,
- PR annotations and organizational reporting,
- team-level history and support.

### Enterprise

Potential enterprise layer after pilot evidence:

- SSO/SAML/SCIM,
- RBAC and delegated policy authority,
- private runners or self-hosted control plane,
- signed attestations and enterprise evidence export,
- retention/data-residency controls,
- validated compliance mapping packs,
- SLA and enterprise support.

### Pricing principle

Do not freeze exact prices before pilots establish willingness-to-pay and cost
to serve. Test a workspace base plus repository/developer band rather than
pricing by Markdown document count.

## 8. ROADMAP

### R0 — Product baseline

Freeze category, ICP, workflow, architecture, domain model, commercial boundary
and non-goals. This document is the proposed R0 canonical source.

### R1 — Self-governance dogfood

Detect and report governance drift in GOVERDOCS itself, including review-date
freshness, state contradictions, missing evidence and repository identity drift.
No automatic canonical repair.

### R2 — Governance Gate R1

Create one read-only/dry-run orchestration path over existing components:

```text
ChangeSet → classify → obligations → validate → GateReport
```

Output deterministic machine-readable and human-readable results with
`PASS/WARN/BLOCKED` and evidence references.

### R3 — GitHub adapter

Map `GateReport` to a GitHub check/annotation workflow. GitHub remains the merge
enforcement authority.

### R4 — Approval and receipt binding

Resolve approval identity/freshness for exact PR/SHA state and produce complete
receipts.

### R5 — Governed AI drafting

Allow an approved obligation to request a bounded AI draft that produces a
patch, passes deterministic validation and remains subject to human approval.

### R6 — Agent interfaces

Expose read/evaluate/explain capabilities through standard agent interfaces
such as MCP/skills without giving the agent implicit canonical-write authority.

### R7 — External pilots

Pilot on at least one repository outside GOVERDOCS and measure false positives,
false negatives, time-to-value, remediation time, developer friction and audit
preparation effort.

### R8 — Hosted team and enterprise plane

Build centralized service capabilities only if pilot evidence demonstrates a
recurring multi-repository coordination problem and willingness to pay.

## 9. NON_GOALS

Until separately justified by evidence, do not build:

- a documentation editor/hosting platform,
- a general developer portal or service catalog,
- a replacement for GitHub/GitLab merge authorization,
- a general CI/CD platform,
- a custom cryptographic signing standard,
- a universal policy programming language,
- a graph database as a prerequisite,
- a universal workflow engine,
- microservices for the local kernel,
- an autonomous AI agent with canonical write/approval authority,
- broad compliance claims without validated mappings and qualified review.

## 10. PRODUCT_SUCCESS_AND_GATES

### North-star metric

`Verified Change Coverage (VCC)` = percentage of material evaluated changes for
which relevant obligations were identified, blocking evidence was satisfied,
required approvals were bound to the exact state and contradictions were
resolved before advancement.

Supporting metrics:

- false-positive rate,
- false-negative rate,
- time to governed decision,
- governance drift detection time,
- remediation lead time,
- evidence completeness,
- audit preparation effort,
- developer friction,
- pilot adoption and retention.

No product-success claim is `VERIFIED` until measured in real use against an
explicit baseline.

## 11. FIRST_IMPLEMENTATION_SLICE

The first implementation PR derived from this baseline is **Governance Gate R1**.

Required behavior:

- one CLI/library orchestration entry point,
- read-only/dry-run only,
- reuse existing classifier, decision matrix, planner and validator,
- deterministic `GateReport`,
- `PASS/WARN/BLOCKED` status,
- explicit obligations, rationale and evidence gaps,
- JSON output suitable for CI plus concise human output,
- no network dependency for the kernel,
- no canonical writes, commit, push, merge, release or deployment,
- tests for deterministic output, failure cases and no-write behavior.

Acceptance target:

```text
same input + same policy version = same GateReport
missing blocking evidence = BLOCKED
non-blocking freshness issue = WARN
all blocking obligations satisfied = PASS
```

This slice is intentionally smaller than an AI writer, GitHub App or hosted
control plane because it validates the core product hypothesis with the least
irreversible complexity.
