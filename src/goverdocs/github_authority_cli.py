from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .authority import AuthorityPolicyError, apply_authority_policy, load_authority_policy
from .config import load_config
from .evidence import load_json_records, validate_record
from .github_check import (
    DEFAULT_CHECK_NAME,
    GitHubChecksRESTClient,
    build_check_run_payload,
    publish_gate_check,
)
from .github_runner import GitHubGovernanceRunError, run_github_pr_governance
from .github_source import GitHubRESTClient, collect_pull_observation


def _parse_role_binding(value: str) -> tuple[str, str]:
    login, separator, role = value.partition("=")
    if not separator or not login.strip() or not role.strip():
        raise argparse.ArgumentTypeError("role binding must use LOGIN=ROLE")
    return login.strip(), role.strip()


def _digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="goverdocs-github-authority-run",
        description=(
            "Compose canonical GitHub governance evaluation, then apply R11 "
            "multi-actor authority before publishing the required check"
        ),
    )
    parser.add_argument("--root", default=".", help="GOVERDOCS project root")
    parser.add_argument(
        "--authority-policy",
        default="policies/AUTHORITY_POLICY.yaml",
        help="R11 authority policy path, relative to --root unless absolute",
    )
    parser.add_argument(
        "--repository",
        required=True,
        help="GitHub repository in owner/name form",
    )
    parser.add_argument(
        "--pull-request",
        required=True,
        type=int,
        help="Pull request number",
    )
    parser.add_argument(
        "--as-of",
        required=True,
        help="Deterministic evaluation date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--verified-at",
        help="Explicit verifier timestamp; defaults to end of --as-of day",
    )
    parser.add_argument(
        "--role-binding",
        action="append",
        default=[],
        type=_parse_role_binding,
        help="Explicit GitHub LOGIN=governance-role binding; repeatable",
    )
    parser.add_argument(
        "--evidence-file",
        action="append",
        default=[],
        help="JSON EvidenceItem input; repeatable",
    )
    parser.add_argument(
        "--approval-file",
        action="append",
        default=[],
        help="JSON Approval input; repeatable",
    )
    parser.add_argument(
        "--trusted-verifier",
        action="append",
        default=[],
        help="Explicit trusted verifier id; repeatable",
    )
    parser.add_argument(
        "--trust-github-verifier",
        action="store_true",
        help="Trust github-rest-source-v1 for records generated during this run",
    )
    parser.add_argument(
        "--trust-pr-evidence-contract",
        action="store_true",
        help=(
            "Trust github-pr-evidence-contract-v1 for PR declaration evidence "
            "generated during this run"
        ),
    )
    parser.add_argument(
        "--trust-project-owner-comment-approval",
        action="store_true",
        help=(
            "Trust strict GOVERDOCS-APPROVAL-V1 COMMENT reviews from explicitly "
            "role-bound project owners"
        ),
    )
    parser.add_argument("--check-name", default=DEFAULT_CHECK_NAME)
    parser.add_argument("--details-url")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish the authority-adjusted GateReport as a GitHub Check Run",
    )
    parser.add_argument("--api-url", default="https://api.github.com")
    parser.add_argument("--api-version", default="2022-11-28")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = Path(args.root).expanduser().resolve()
        policy_path = Path(args.authority_policy).expanduser()
        if not policy_path.is_absolute():
            policy_path = root / policy_path
        authority_policy = load_authority_policy(policy_path)

        role_bindings = dict(args.role_binding)
        if len(role_bindings) != len(args.role_binding):
            raise ValueError("duplicate GitHub role binding login")

        configured_roles = set(authority_policy["roles"])
        unknown_roles = sorted(set(role_bindings.values()) - configured_roles)
        if unknown_roles:
            raise AuthorityPolicyError(
                "GitHub role binding references roles absent from authority policy: "
                + ", ".join(unknown_roles)
            )

        config = load_config(root)
        reader = GitHubRESTClient.from_env(
            args.token_env,
            api_url=args.api_url,
            api_version=args.api_version,
        )

        base_result = run_github_pr_governance(
            reader,
            config=config,
            repository=args.repository,
            pull_request=args.pull_request,
            as_of=date.fromisoformat(args.as_of),
            role_bindings=role_bindings,
            evidence_items=load_json_records(args.evidence_file),
            approvals=load_json_records(args.approval_file),
            trusted_verifiers=set(args.trusted_verifier),
            trust_github_verifier=bool(args.trust_github_verifier),
            trust_pr_evidence_contract=bool(args.trust_pr_evidence_contract),
            trust_project_owner_comment_approval=bool(
                args.trust_project_owner_comment_approval
            ),
            verified_at=args.verified_at,
            publish=False,
            check_name=args.check_name,
            details_url=args.details_url,
        )

        receipt = dict(base_result["run_receipt"])
        expected_head = str(receipt["head_sha"])
        expected_base = str(receipt["base_sha"])
        observation = collect_pull_observation(
            reader,
            repository=args.repository,
            pull_request=args.pull_request,
        )
        if observation["head_sha"] != expected_head:
            raise GitHubGovernanceRunError(
                "pull request HEAD changed during authority evaluation"
            )
        if observation["base_sha"] != expected_base:
            raise GitHubGovernanceRunError(
                "pull request base changed during authority evaluation"
            )

        author = observation.get("author")
        if not isinstance(author, dict):
            raise GitHubGovernanceRunError(
                "GitHub pull observation is missing author"
            )
        author_login = str(author.get("login") or "")
        report = apply_authority_policy(
            base_result["gate_report"],
            change_author=author_login,
            policy=authority_policy,
        )
        payload = build_check_run_payload(
            report,
            expected_repository=args.repository,
            expected_head_sha=expected_head,
            check_name=args.check_name,
            details_url=args.details_url,
        )

        publication_receipt = None
        if args.publish:
            writer = GitHubChecksRESTClient.from_env(
                args.token_env,
                api_url=args.api_url,
                api_version=args.api_version,
            )
            publication_receipt = publish_gate_check(
                writer,
                report,
                expected_repository=args.repository,
                expected_head_sha=expected_head,
                check_name=args.check_name,
                details_url=args.details_url,
            )

        receipt["gate_status"] = str(report["status"])
        receipt["gate_report_digest"] = _digest(report)
        receipt["check_conclusion"] = str(payload["conclusion"])
        receipt["published"] = bool(args.publish)
        receipt["publication_receipt"] = publication_receipt
        errors = validate_record(
            receipt,
            "github-governance-run.schema.json",
        )
        if errors:
            raise GitHubGovernanceRunError(
                "authority-adjusted GitHub governance run receipt validation failed: "
                + "; ".join(errors)
            )

        result = {
            "run_receipt": receipt,
            "gate_report": report,
            "check_run_payload": payload,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if report["status"] == "BLOCKED" else 0
    except (
        FileNotFoundError,
        AuthorityPolicyError,
        GitHubGovernanceRunError,
        RuntimeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
