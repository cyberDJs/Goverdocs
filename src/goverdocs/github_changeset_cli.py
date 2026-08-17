from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from .github_changeset import collect_pull_changeset_observation
from .github_source import GitHubRESTClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="goverdocs-github-changeset",
        description="Read-only GitHub pull-request ChangeSet source adapter for GOVERDOCS",
    )
    parser.add_argument("--repository", required=True, help="GitHub repository in owner/name form")
    parser.add_argument("--pull-request", required=True, type=int, help="Pull request number")
    parser.add_argument("--api-url", default="https://api.github.com", help="GitHub REST API base URL")
    parser.add_argument("--api-version", default="2022-11-28", help="GitHub REST API version header")
    parser.add_argument("--token-env", default="GITHUB_TOKEN", help="Environment variable containing an optional GitHub token")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = GitHubRESTClient.from_env(
            args.token_env,
            api_url=args.api_url,
            api_version=args.api_version,
        )
        observation = collect_pull_changeset_observation(
            client,
            repository=args.repository,
            pull_request=args.pull_request,
        )
        print(json.dumps(observation, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
