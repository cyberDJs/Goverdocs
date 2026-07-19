---
id: GOV-DOC-MATRIX
type: governance-matrix
title: Documentation Decision Matrix
status: accepted
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
  - GOV-0001
source_refs:
  - EPIC-0001
last_verified: 2026-07-19
review_due: null
---

# Documentation Decision Matrix

Autoritativní strojově čitelná verze je `documentation_decision_matrix.yaml`.

| Event ID | Událost | Závažnost | Priorita | Primární dokument | Sekundární dokumenty | Approval |
|---|---|---:|---:|---|---|---|
| DOC-EVT-001 | `project_created` | high | 90 | `PROJECT_STATE.md` | DOCUMENTATION_INDEX.md, project-memory/CURRENT_CONTEXT.md, project-memory/SESSION_LOG.md | NE |
| DOC-EVT-002 | `project_state_changed` | medium | 30 | `PROJECT_STATE.md` | project-memory/CURRENT_CONTEXT.md, project-memory/SESSION_LOG.md | NE |
| DOC-EVT-003 | `work_block_started` | medium | 35 | `docs/work-blocks/active/WB-*.md` | project-memory/ACTIVE_WORK.md, project-memory/SESSION_LOG.md | NE |
| DOC-EVT-004 | `work_block_completed` | medium | 40 | `docs/work-blocks/completed/WB-*.md` | project-memory/ACTIVE_WORK.md, PROJECT_STATE.md, project-memory/SESSION_LOG.md | ANO |
| DOC-EVT-005 | `work_block_blocked` | medium | 45 | `docs/work-blocks/active/WB-*.md` | project-memory/ACTIVE_WORK.md, project-memory/OPEN_QUESTIONS.md | NE |
| DOC-EVT-006 | `open_question_created` | low | 20 | `project-memory/OPEN_QUESTIONS.md` | project-memory/SESSION_LOG.md | NE |
| DOC-EVT-007 | `open_question_closed` | low | 20 | `project-memory/OPEN_QUESTIONS.md` | project-memory/CURRENT_CONTEXT.md | NE |
| DOC-EVT-008 | `decision_accepted` | high | 70 | `docs/decisions/**/ADR-*.md` | project-memory/DECISIONS_REGISTER.md, DOCUMENTATION_INDEX.md | ANO |
| DOC-EVT-009 | `accepted_decision_changed` | critical | 95 | `docs/decisions/**/ADR-*.md` | project-memory/DECISIONS_REGISTER.md, docs/reviews/REV-*.md | ANO |
| DOC-EVT-010 | `adr_superseded` | high | 85 | `docs/decisions/**/ADR-*.md` | project-memory/DECISIONS_REGISTER.md, manifests/RELATIONSHIP_GRAPH.json | ANO |
| DOC-EVT-011 | `architecture_change` | high | 80 | `docs/architecture/ARCH-*.md` | docs/decisions/architecture/ADR-*.md, PROJECT_STATE.md, project-memory/SESSION_LOG.md | ANO |
| DOC-EVT-012 | `component_responsibility_change` | high | 75 | `docs/architecture/ARCH-*.md` | docs/decisions/architecture/ADR-*.md, manifests/RELATIONSHIP_GRAPH.json | ANO |
| DOC-EVT-013 | `integration_interface_change` | high | 75 | `docs/architecture/ARCH-*.md` | docs/decisions/architecture/ADR-*.md, docs/operations/OPS-*.md | ANO |
| DOC-EVT-014 | `api_contract_change` | high | 78 | `docs/architecture/ARCH-*.md` | docs/decisions/architecture/ADR-*.md, generated/RELEASE_NOTES.md | ANO |
| DOC-EVT-015 | `data_model_change` | high | 76 | `docs/architecture/ARCH-*.md` | docs/decisions/architecture/ADR-*.md, docs/operations/OPS-*.md | ANO |
| DOC-EVT-016 | `security_boundary_change` | critical | 100 | `docs/security/SEC-*.md` | docs/decisions/security/ADR-*.md, docs/reviews/REV-*.md, PROJECT_STATE.md | ANO |
| DOC-EVT-017 | `authentication_authorization_change` | critical | 100 | `docs/security/SEC-*.md` | docs/decisions/security/ADR-*.md, docs/operations/OPS-*.md | ANO |
| DOC-EVT-018 | `secrets_handling_change` | critical | 100 | `docs/security/SEC-*.md` | docs/decisions/security/ADR-*.md, docs/reviews/REV-*.md | ANO |
| DOC-EVT-019 | `security_incident` | critical | 110 | `docs/security/incidents/INC-*.md` | evidence/incidents/**, docs/work-blocks/active/WB-*.md, PROJECT_STATE.md | ANO |
| DOC-EVT-020 | `security_vulnerability_fixed` | critical | 105 | `docs/security/SEC-*.md` | docs/security/incidents/INC-*.md, docs/reviews/REV-*.md, generated/RELEASE_NOTES.md | ANO |
| DOC-EVT-021 | `epic_created` | medium | 50 | `docs/epics/active/EPIC-*.md` | PROJECT_STATE.md, DOCUMENTATION_INDEX.md | ANO |
| DOC-EVT-022 | `epic_scope_changed` | high | 60 | `docs/epics/active/EPIC-*.md` | docs/decisions/product/ADR-*.md, PROJECT_STATE.md | ANO |
| DOC-EVT-023 | `epic_closed` | medium | 55 | `docs/epics/{completed,cancelled}/EPIC-*.md` | PROJECT_STATE.md, project-memory/SESSION_LOG.md | ANO |
| DOC-EVT-024 | `deployment_change` | high | 70 | `docs/operations/OPS-*.md` | docs/decisions/infrastructure/ADR-*.md, PROJECT_STATE.md | ANO |
| DOC-EVT-025 | `cicd_change` | high | 68 | `docs/operations/OPS-*.md` | docs/decisions/infrastructure/ADR-*.md, docs/reviews/REV-*.md | ANO |
| DOC-EVT-026 | `infrastructure_change` | high | 72 | `docs/operations/OPS-*.md` | docs/decisions/infrastructure/ADR-*.md, docs/architecture/ARCH-*.md | ANO |
| DOC-EVT-027 | `environment_configuration_change` | medium | 58 | `docs/operations/OPS-*.md` | project-memory/CURRENT_CONTEXT.md, project-memory/SESSION_LOG.md | ANO |
| DOC-EVT-028 | `dependency_change` | medium | 55 | `docs/operations/OPS-*.md` | docs/reviews/REV-*.md, project-memory/SESSION_LOG.md | ANO |
| DOC-EVT-029 | `breaking_change` | critical | 98 | `docs/decisions/architecture/ADR-*.md` | docs/operations/OPS-*.md, generated/RELEASE_NOTES.md, PROJECT_STATE.md | ANO |
| DOC-EVT-030 | `governance_change` | critical | 92 | `docs/governance/GOV-*.md` | docs/decisions/governance/ADR-*.md, docs/reviews/REV-*.md | ANO |
| DOC-EVT-031 | `runbook_change` | medium | 52 | `docs/operations/OPS-*.md` | project-memory/SESSION_LOG.md | ANO |
| DOC-EVT-032 | `technical_debt_created` | medium | 46 | `project-memory/OPEN_QUESTIONS.md` | docs/work-blocks/active/WB-*.md, docs/reviews/REV-*.md | ANO |
| DOC-EVT-033 | `technical_debt_removed` | medium | 46 | `project-memory/OPEN_QUESTIONS.md` | docs/work-blocks/completed/WB-*.md, project-memory/SESSION_LOG.md | ANO |
| DOC-EVT-034 | `roadmap_change` | high | 65 | `PROJECT_STATE.md` | docs/epics/**/EPIC-*.md, docs/decisions/product/ADR-*.md | ANO |
| DOC-EVT-035 | `release_created` | high | 74 | `generated/RELEASE_NOTES.md` | evidence/releases/**, PROJECT_STATE.md, project-memory/SESSION_LOG.md | ANO |
| DOC-EVT-036 | `release_rollback` | critical | 96 | `docs/operations/OPS-*.md` | evidence/releases/**, PROJECT_STATE.md, docs/reviews/REV-*.md | ANO |
| DOC-EVT-037 | `audit_review_created` | medium | 48 | `docs/reviews/REV-*.md` | project-memory/OPEN_QUESTIONS.md, DOCUMENTATION_INDEX.md | ANO |
| DOC-EVT-038 | `document_changed` | low | 15 | `DOCUMENTATION_INDEX.md` | manifests/DOCUMENT_REGISTRY.yaml, project-memory/SESSION_LOG.md | NE |
| DOC-EVT-039 | `duplicate_detected` | high | 62 | `docs/reviews/REV-*.md` | project-memory/OPEN_QUESTIONS.md | ANO |
| DOC-EVT-040 | `broken_link_detected` | medium | 42 | `docs/reviews/REV-*.md` | DOCUMENTATION_INDEX.md | NE |
| DOC-EVT-041 | `metadata_missing` | high | 64 | `docs/reviews/REV-*.md` | project-memory/OPEN_QUESTIONS.md | ANO |
| DOC-EVT-042 | `document_conflict_detected` | critical | 94 | `docs/reviews/REV-*.md` | project-memory/OPEN_QUESTIONS.md, project-memory/CURRENT_CONTEXT.md | ANO |
| DOC-EVT-043 | `session_started` | low | 10 | `project-memory/SESSION_LOG.md` | project-memory/CURRENT_CONTEXT.md, project-memory/ACTIVE_WORK.md | NE |
| DOC-EVT-044 | `session_ended` | low | 12 | `project-memory/SESSION_LOG.md` | project-memory/CURRENT_CONTEXT.md, PROJECT_STATE.md | NE |
| DOC-EVT-045 | `external_decision_imported` | high | 66 | `docs/decisions/**/ADR-*.md` | project-memory/DECISIONS_REGISTER.md, docs/reviews/REV-*.md | ANO |
