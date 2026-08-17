from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from .github_enforcement import (
    GITHUB_ACTIONS_APP_ID,
    GOVERNANCE_CHECK_CONTEXT,
    collect_effective_enforcement,
)
from .github_source import GitHubRESTClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="goverdocs-github-enforcement",
        description="Verify that GitHub actively requires the GOVERDOCS governance check for a branch.",
    )
    parser.add_argument("--repository", required=True, help="GitHub repository in owner/name form")
    parser.add_argument("--branch", default="main", help="Branch to verify (default: main)")
    parser.add_argument(
        "--required-check",
        default=GOVERNANCE_CHECK_CONTEXT,
        help=f"Required check context (default: {GOVERNANCE_CHECK_CONTEXT})",
    )
    parser.add_argument(
        "--integration-id",
        type=int,
        default=GITHUB_ACTIONS_APP_ID,
        help=f"Required GitHub App integration id (default: {GITHUB_ACTIONS_APP_ID})",
    )
    parser.add_argument(
        "--allow-any-source",
        action="store_true",
        help="Accept the required check without binding it to a specific GitHub App.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    reader = GitHubRESTClient.from_env()
    observation = collect_effective_enforcement(
        reader,
        repository=args.repository,
        branch=args.branch,
    )
    required_integration_id = None if args.allow_any_source else args.integration_id
    payload = observation.as_dict(
        required_context=args.required_check,
        required_integration_id=required_integration_id,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
