from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any

from .config import GoverdocsConfig
from .evidence import validate_record
from .gate import evaluate_gate
from .github_changeset import collect_pull_changeset_observation, gate_input_from_changeset_observation
from .github_check import (
    DEFAULT_CHECK_NAME,
    GitHubCheckWriter,
    build_check_run_payload,
    publish_gate_check,
)
from .github_pr_evidence import VERIFIER_ID as PR_EVIDENCE_VERIFIER_ID
from .github_pr_evidence import (
    collect_pull_evidence_contract,
    evidence_records_from_pr_contract,
)
from .github_project_owner_approval import VERIFIER_ID as PROJECT_OWNER_COMMENT_VERIFIER_ID
from .github_project_owner_approval import project_owner_comment_approval_records
from .github_source import GitHubReader, collect_pull_observation
from .github_verifier import (
    VERIFIER_ID,
    approved_review_records,
    source_reference_evidence,
)


class GitHubGovernanceRunError(RuntimeError):
    pass


def _digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_same_subject(changeset: dict[str, Any], observation: dict[str, Any]) -> None:
    for key in ("repository", "pull_request", "head_sha", "base_sha"):
        if changeset.get(key) != observation.get(key):
            raise GitHubGovernanceRunError(f"GitHub source observations disagree on {key}")


def _evaluate(
    config: GoverdocsConfig,
    *,
    gate_input: dict[str, Any],
    as_of: date,
    evidence_items: list[dict[str, Any]],
    approvals: list[dict[str, Any]],
    trusted_verifiers: set[str],
) -> dict[str, Any]:
    return evaluate_gate(
        root=config.root,
        policy_path=config.policy_path,
        matrix_path=config.matrix_path,
        metadata_schema_path=config.metadata_schema_path,
        change_gate_path=config.change_gate_path,
        change_gate_schema_path=config.change_gate_schema_path,
        changed_files=list(gate_input["changed_files"]),
        diff_text=str(gate_input["diff_text"]),
        as_of=as_of,
        repository=str(gate_input["repository"]),
        pull_request=int(gate_input["pull_request"]),
        head_sha=str(gate_input["head_sha"]),
        evidence_items=evidence_items,
        approvals=approvals,
        trusted_verifiers=trusted_verifiers,
    )


def _generated_github_records(
    observation: dict[str, Any],
    preliminary_report: dict[str, Any],
    *,
    role_bindings: dict[str, str],
    identity_bindings: dict[str, dict[str, str]] | None,
    verified_at: str,
    include_project_owner_comment_approval: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_input = preliminary_report.get("input")
    if not isinstance(raw_input, dict):
        raise GitHubGovernanceRunError("preliminary GateReport is missing input")
    raw_change_digest = raw_input.get("change_digest")
    if not isinstance(raw_change_digest, str) or len(raw_change_digest) != 64:
        raise GitHubGovernanceRunError("preliminary GateReport change digest is invalid")

    evidence: list[dict[str, Any]] = []
    approvals: list[dict[str, Any]] = []
    for raw_obligation in preliminary_report.get("obligations", []):
        if not isinstance(raw_obligation, dict):
            continue
        rule_id = str(raw_obligation.get("rule_id") or "")
        event = str(raw_obligation.get("event") or "")
        if not rule_id:
            continue

        source_record = source_reference_evidence(
            observation,
            rule_id=rule_id,
            change_digest=raw_change_digest,
            verified_at=verified_at,
        )
        source_record["evidence_id"] = f"{source_record['evidence_id']}-{rule_id.lower()}"
        evidence.append(source_record)

        if bool(raw_obligation.get("approval_required")):
            records = approved_review_records(
                observation,
                rule_id=rule_id,
                approval_type=event or rule_id,
                change_digest=raw_change_digest,
                role_bindings=role_bindings,
                identity_bindings=identity_bindings,
                verified_at=verified_at,
            )
            if include_project_owner_comment_approval:
                records.extend(
                    project_owner_comment_approval_records(
                        observation,
                        rule_id=rule_id,
                        approval_type=event or rule_id,
                        change_digest=raw_change_digest,
                        role_bindings=role_bindings,
                        identity_bindings=identity_bindings,
                        verified_at=verified_at,
                    )
                )
            for record in records:
                record["approval_id"] = f"{record['approval_id']}-{rule_id.lower()}"
                approvals.append(record)

    evidence.sort(key=lambda item: str(item["evidence_id"]))
    approvals.sort(key=lambda item: str(item["approval_id"]))
    return evidence, approvals


def run_github_pr_governance(
    reader: GitHubReader,
    *,
    config: GoverdocsConfig,
    repository: str,
    pull_request: int,
    as_of: date,
    role_bindings: dict[str, str] | None = None,
    identity_bindings: dict[str, dict[str, str]] | None = None,
    evidence_items: list[dict[str, Any]] | None = None,
    approvals: list[dict[str, Any]] | None = None,
    trusted_verifiers: set[str] | None = None,
    trust_github_verifier: bool = False,
    trust_pr_evidence_contract: bool = False,
    trust_project_owner_comment_approval: bool = False,
    verified_at: str | None = None,
    writer: GitHubCheckWriter | None = None,
    publish: bool = False,
    check_name: str = DEFAULT_CHECK_NAME,
    details_url: str | None = None,
) -> dict[str, Any]:
    if publish and writer is None:
        raise GitHubGovernanceRunError("publish=True requires a GitHub Check writer")

    role_bindings = role_bindings or {}
    evidence_items = list(evidence_items or [])
    approvals = list(approvals or [])
    trusted = set(trusted_verifiers or set())
    verification_time = verified_at or f"{as_of.isoformat()}T23:59:59Z"

    changeset = collect_pull_changeset_observation(
        reader,
        repository=repository,
        pull_request=pull_request,
    )
    gate_input = gate_input_from_changeset_observation(changeset)

    observation = collect_pull_observation(
        reader,
        repository=repository,
        pull_request=pull_request,
    )
    _assert_same_subject(changeset, observation)

    preliminary = _evaluate(
        config,
        gate_input=gate_input,
        as_of=as_of,
        evidence_items=evidence_items,
        approvals=approvals,
        trusted_verifiers=trusted,
    )
    generated_evidence, generated_approvals = _generated_github_records(
        observation,
        preliminary,
        role_bindings=role_bindings,
        identity_bindings=identity_bindings,
        verified_at=verification_time,
        include_project_owner_comment_approval=trust_project_owner_comment_approval,
    )

    pr_evidence_contract = collect_pull_evidence_contract(
        reader,
        repository=repository,
        pull_request=pull_request,
        expected_head_sha=str(gate_input["head_sha"]),
        expected_base_sha=str(changeset["base_sha"]),
    )
    generated_pr_contract_evidence = evidence_records_from_pr_contract(
        pr_evidence_contract,
        preliminary,
        verified_at=verification_time,
    )

    if trust_github_verifier:
        trusted.add(VERIFIER_ID)
    if trust_pr_evidence_contract:
        trusted.add(PR_EVIDENCE_VERIFIER_ID)
    if trust_project_owner_comment_approval:
        trusted.add(PROJECT_OWNER_COMMENT_VERIFIER_ID)

    report = _evaluate(
        config,
        gate_input=gate_input,
        as_of=as_of,
        evidence_items=[*evidence_items, *generated_evidence, *generated_pr_contract_evidence],
        approvals=[*approvals, *generated_approvals],
        trusted_verifiers=trusted,
    )
    payload = build_check_run_payload(
        report,
        expected_repository=repository,
        expected_head_sha=str(gate_input["head_sha"]),
        check_name=check_name,
        details_url=details_url,
    )

    publication_receipt: dict[str, Any] | None = None
    if publish:
        assert writer is not None
        publication_receipt = publish_gate_check(
            writer,
            report,
            expected_repository=repository,
            expected_head_sha=str(gate_input["head_sha"]),
            check_name=check_name,
            details_url=details_url,
        )

    run_receipt: dict[str, Any] = {
        "schema_version": 1,
        "repository": repository,
        "pull_request": pull_request,
        "head_sha": str(gate_input["head_sha"]),
        "base_sha": str(changeset["base_sha"]),
        "evaluation_date": as_of.isoformat(),
        "changeset_source_digest": str(changeset["source_digest"]),
        "github_observation_digest": _digest(observation),
        "pr_evidence_contract_digest": str(pr_evidence_contract["source_digest"]),
        "generated_evidence_ids": sorted(
            [
                *(str(item["evidence_id"]) for item in generated_evidence),
                *(str(item["evidence_id"]) for item in generated_pr_contract_evidence),
            ]
        ),
        "generated_pr_contract_evidence_ids": [
            str(item["evidence_id"]) for item in generated_pr_contract_evidence
        ],
        "generated_approval_ids": [str(item["approval_id"]) for item in generated_approvals],
        "trusted_verifiers": sorted(trusted),
        "gate_status": str(report["status"]),
        "gate_report_digest": _digest(report),
        "check_name": check_name,
        "check_conclusion": str(payload["conclusion"]),
        "published": publish,
        "publication_receipt": publication_receipt,
    }
    errors = validate_record(run_receipt, "github-governance-run.schema.json")
    if errors:
        raise GitHubGovernanceRunError(f"GitHub governance run receipt validation failed: {'; '.join(errors)}")

    return {
        "run_receipt": run_receipt,
        "gate_report": report,
        "check_run_payload": payload,
    }
