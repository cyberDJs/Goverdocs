---
id: GOV-0004
type: governance
title: R10 Enforcement Resilience / Bypass and Failure-Mode Proof
status: active
owner: GOVERDOCS
created: 2026-08-17
updated: 2026-08-17
version: 1.1.0
canonical: true
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - GOV-0002
source_refs:
  - GH-ISSUE-27
last_verified: 2026-08-17
review_due: null
---

# R10 — Enforcement Resilience / Bypass & Failure-Mode Proof

## Purpose

R10 proves that the R9 required governance gate remains fail-closed when the repository is exposed to stale state, missing checks, approval lifecycle changes, and governance execution failure.

The authority for every negative proof is GitHub's server-side branch update or pull-request merge rejection. A local evaluator result alone is not sufficient.

## Canonical enforcement baseline

Repository: `nulleimy/Goverdocs`

Protected target: `refs/heads/main`

Required status check: `GOVERDOCS Governance Gate`

Expected producer: GitHub Actions integration `15368`

Active ruleset: `20928616`

Strict required status checks policy: `true`

Bypass actors: none.

## Verified R10 invariants

### R10.1 — missing-check fail-closed — PASS

A direct Contents API update attempted to create `docs/probes/r10-missing-check-direct-update.md` on `main` before the new commit could possess the required check.

GitHub rejected the branch update with HTTP `409` and the repository-rule reason:

`Required status check "GOVERDOCS Governance Gate" is expected.`

The probe never reached `main`.

### R10.2 — stale-branch fail-closed — PASS

Disposable PR `#28` used exact head `1216ab96c9330e25b823b995712a135fb6ffb4a8` against base `eab7b970058c75a5bcfffe71df2947f8f27ea95f`.

Before the base moved, required check `95302002900` was `PASS` / `success` / zero gaps. Canonical R10 contract PR `#29` then advanced `main` to `471d08d7e7db712a1519db7700bc84e29ac3d6b2` without changing the candidate head.

GitHub rejected the exact-head merge with HTTP `405` because `GOVERDOCS Governance Gate` was `expected` again. The earlier PASS could not be reused against the newer base. PR `#28` was closed unmerged.

### R10.3 — approval/head binding — PASS

Disposable PR `#30` established H1 `0b852ca59fa6338f2fcb7fa2dceb13f4d0e1a923`.

H1 was initially BLOCKED. Exact-H1 project-owner review `4948952374` then produced required check `95303418007` = `PASS` / `success` / zero gaps.

The same governed file was changed to H2 `c80d54572d6f63430e8207d2f6bf9da0a4013fc4` while the H1 approval remained in review history. H2 check `95303562783` returned `BLOCKED` / `failure` with `APPROVAL_REQUIRED` and `no bound approval record`.

GitHub rejected the exact-H2 merge with HTTP `405` because the required governance check was failing. The H1 approval did not transfer to H2. PR `#30` was closed unmerged.

### R10.4 — exact-head approval revocation — PASS

GitHub cannot dismiss a COMMENTED review, so the original R10.4 dismissal experiment exposed an approval-lifecycle transport gap. Focused repair PR `#31` added strict exact-subject `decision=approved|revoked` semantics while preserving whole-body markers, explicit project-owner role binding, exact PR/head/commit binding, and actor scoping.

The repair became canonical at `main@eb14222fe1f39abd44dfa47535246d704b4335ce`.

Fresh disposable PR `#32` then held one unchanged exact head:

`cb39325bf546d875423ed3d68ec6446a871d12ac`

Observed lifecycle:

1. no marker -> check `95304920926` = `BLOCKED` / `failure`;
2. exact-head approval review `4948995941` -> check `95305091873` = `PASS` / `success` / zero gaps;
3. same exact head, later revocation review `4949002588` -> check `95305282311` = `BLOCKED` / `failure` with approval required.

GitHub then rejected the exact-head merge with HTTP `405` because `GOVERDOCS Governance Gate` was failing. PR `#32` was closed unmerged.

### R10.5 — governance execution failure fail-closed — PASS

Disposable PR `#33` used exact head `fbff88e8a06e22f41b4604426adcc1008e5dbed9` and one binary/NUL probe file `r10/workflow-failure-probe.bin`.

GitHub's PR Files API omitted the textual `patch`. Canonical ChangeSet acquisition therefore became incomplete. Governance workflow run `32002634517`, job `95305798705`, failed in `Evaluate PR and publish GOVERDOCS Check` with:

`ERROR: GitHub ChangeSet observation is incomplete: one_or_more_patches_unavailable`

The workflow failed before publishing the required context: the exact head had zero `GOVERDOCS Governance Gate` check runs.

GitHub rejected the exact-head merge with HTTP `405` and:

`Required status check "GOVERDOCS Governance Gate" is expected.`

PR `#33` was closed unmerged and the binary probe never reached `main`.

## Approval revocation contract

For each explicitly role-bound project-owner actor and exact PR+HEAD subject, only that actor's latest valid `GOVERDOCS-APPROVAL-V1` COMMENT marker is authoritative.

Supported decisions:

- `decision=approved` — authorize the exact subject;
- `decision=revoked` — withdraw that actor's authorization for the exact subject.

A later approval may explicitly re-authorize after revocation. Normal comments, wrong-role actors, wrong PR numbers, stale heads, non-COMMENTED reviews, partial-body markers, or mismatched review commit IDs remain ineligible.

## Proof discipline

R10 preserved these controls throughout:

- ruleset `20928616` was not weakened;
- no bypass actor was introduced;
- no force merge was used;
- exact-head merge guards were used for intended positive merges;
- negative proof PRs were closed unmerged;
- canonical changes passed quality, CodeQL and review-thread verification before merge;
- known non-blocking `DOC-EVT-011` classifier/matrix drift was not masked or expanded into classifier feature work.

## Completion condition

All five R10 invariants now have live GitHub server-side evidence. R10 may be declared complete only after this evidence reconciliation itself is merged through the active required governance rule, post-merge quality and CodeQL are green, and effective rules for `main` still show ruleset `20928616` requiring `GOVERDOCS Governance Gate` from integration `15368` in strict mode.
