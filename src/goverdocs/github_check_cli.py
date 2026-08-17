from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .github_check import (
    DEFAULT_CHECK_NAME,
    GitHubChecksRESTClient,
    build_check_run_payload,
    publish_gate_check,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="goverdocs-github-check",
        description="Publish a GOVERDOCS GateReport as a GitHub Check Run; dry-run unless --publish is explicit",
    )
    parser.add_argument("--gate-report", required=True, help="Path to a GateReport v2 JSON file")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"), help="Expected GitHub owner/name; defaults to GITHUB_REPOSITORY")
    parser.add_argument("--head-sha", default=os.environ.get("GITHUB_SHA"), help="Expected exact Git head SHA; defaults to GITHUB_SHA")
    parser.add_argument("--check-name", default=DEFAULT_CHECK_NAME, help="GitHub Check Run name")
    parser.add_argument("--details-url", default=None, help="Optional URL with full GateReport details")
    parser.add_argument("--api-url", default="https://api.github.com", help="GitHub REST API base URL")
    parser.add_argument("--api-version", default="2022-11-28", help="GitHub REST API version header")
    parser.add_argument("--token-env", default="GITHUB_TOKEN", help="Environment variable containing a token with Checks: write")
    parser.add_argument("--publish", action="store_true", help="Actually create the GitHub Check Run; otherwise print the deterministic payload")
    return parser


def _load_report(raw_path: str) -> dict[str, Any]:
    path = Path(raw_path).expanduser().resolve()
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("GateReport JSON must be an object")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if not args.repository:
            raise ValueError("--repository or GITHUB_REPOSITORY is required")
        if not args.head_sha:
            raise ValueError("--head-sha or GITHUB_SHA is required")

        report = _load_report(args.gate_report)
        payload = build_check_run_payload(
            report,
            expected_repository=args.repository,
            expected_head_sha=args.head_sha,
            check_name=args.check_name,
            details_url=args.details_url,
        )
        if not args.publish:
            print(
                json.dumps(
                    {
                        "mode": "dry-run",
                        "repository": args.repository,
                        "payload": payload,
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        client = GitHubChecksRESTClient.from_env(
            args.token_env,
            api_url=args.api_url,
            api_version=args.api_version,
        )
        receipt = publish_gate_check(
            client,
            report,
            expected_repository=args.repository,
            expected_head_sha=args.head_sha,
            check_name=args.check_name,
            details_url=args.details_url,
        )
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
