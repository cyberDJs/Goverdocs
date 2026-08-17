from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .config import load_config
from .evidence import load_json_records
from .github_check import DEFAULT_CHECK_NAME, GitHubChecksRESTClient
from .github_runner import GitHubGovernanceRunError, run_github_pr_governance
from .github_source import GitHubRESTClient


def _parse_role_binding(value: str) -> tuple[str, str]:
    login, separator, role = value.partition("=")
    if not separator or not login.strip() or not role.strip():
        raise argparse.ArgumentTypeError("role binding must use LOGIN=ROLE")
    return login.strip(), role.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="goverdocs-github-run",
        description="Compose GitHub ChangeSet + evidence observation -> Gate -> GitHub Check",
    )
    parser.add_argument("--root", default=".", help="GOVERDOCS project root")
    parser.add_argument("--repository", required=True, help="GitHub repository in owner/name form")
    parser.add_argument("--pull-request", required=True, type=int, help="Pull request number")
    parser.add_argument("--as-of", required=True, help="Deterministic evaluation date in YYYY-MM-DD")
    parser.add_argument("--verified-at", help="Explicit verifier timestamp; defaults to end of --as-of day")
    parser.add_argument("--role-binding", action="append", default=[], type=_parse_role_binding, help="Explicit GitHub LOGIN=governance-role binding; repeatable")
    parser.add_argument("--evidence-file", action="append", default=[], help="JSON EvidenceItem input; repeatable")
    parser.add_argument("--approval-file", action="append", default=[], help="JSON Approval input; repeatable")
    parser.add_argument("--trusted-verifier", action="append", default=[], help="Explicit trusted verifier id; repeatable")
    parser.add_argument("--trust-github-verifier", action="store_true", help="Trust github-rest-source-v1 for records generated during this run")
    parser.add_argument(
        "--trust-pr-evidence-contract",
        action="store_true",
        help="Trust github-pr-evidence-contract-v1 for PR declaration evidence generated during this run",
    )
    parser.add_argument(
        "--trust-project-owner-comment-approval",
        action="store_true",
        help=(
            "Trust strict GOVERDOCS-APPROVAL-V1 COMMENT reviews from explicitly role-bound project owners; "
            "normal comments never become approvals"
        ),
    )
    parser.add_argument("--check-name", default=DEFAULT_CHECK_NAME)
    parser.add_argument("--details-url")
    parser.add_argument("--publish", action="store_true", help="Publish the resulting GateReport as a GitHub Check Run")
    parser.add_argument("--api-url", default="https://api.github.com")
    parser.add_argument("--api-version", default="2022-11-28")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = Path(args.root).expanduser().resolve()
        config = load_config(root)
        role_bindings = dict(args.role_binding)
        if len(role_bindings) != len(args.role_binding):
            raise ValueError("duplicate GitHub role binding login")

        reader = GitHubRESTClient.from_env(
            args.token_env,
            api_url=args.api_url,
            api_version=args.api_version,
        )
        writer: GitHubChecksRESTClient | None = None
        if args.publish:
            writer = GitHubChecksRESTClient.from_env(
                args.token_env,
                api_url=args.api_url,
                api_version=args.api_version,
            )

        result = run_github_pr_governance(
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
            trust_project_owner_comment_approval=bool(args.trust_project_owner_comment_approval),
            verified_at=args.verified_at,
            writer=writer,
            publish=bool(args.publish),
            check_name=args.check_name,
            details_url=args.details_url,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        status = str(result["gate_report"]["status"])
        return 1 if status == "BLOCKED" else 0
    except (FileNotFoundError, GitHubGovernanceRunError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
