# R9 — Hard Enforcement / Required Governance Check

## Purpose

R9 converts the already-published `GOVERDOCS Governance Gate` from advisory evidence into an active GitHub repository rule for `main`.

The repository-side verifier is intentionally read-only. It observes GitHub's effective active rules for the target branch and fails closed unless the exact required status-check contract is present.

## Canonical required state

Repository: `nulleimy/Goverdocs`

Target branch: `main`

Required check context:

```text
GOVERDOCS Governance Gate
```

Required producer:

```text
GitHub Actions app id = 15368
```

Required status-check policy:

```text
strict_required_status_checks_policy = true
bypass_actors = []
do_not_enforce_on_create = false
```

No review-count, CODEOWNERS, deployment, release, deletion, force-push, linear-history, commit-metadata, or other unrelated policy is part of R9.

## Why a repository ruleset

A repository-level branch ruleset can target only `refs/heads/main` and contain only the `required_status_checks` rule. This keeps the hard-enforcement slice smaller than creating a broad classic branch-protection configuration.

## Activation boundary

Creating or editing repository rulesets requires repository `Administration: write`. The ChatGPT GitHub connector used for R9.0 does not expose that permission or a ruleset-write action.

Therefore R9.1 must be executed by a repository-admin GitHub session or token. R9 must remain `NOT COMPLETE` until the resulting effective rule is independently observed and negative/positive enforcement probes succeed.

## Canonical activation payload

Using GitHub CLI with a repository-admin token/session:

```bash
REPO="nulleimy/Goverdocs"

cat > /tmp/goverdocs-r9-ruleset.json <<'JSON'
{
  "name": "R9 — GOVERDOCS Governance Gate",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "required_status_checks",
      "parameters": {
        "do_not_enforce_on_create": false,
        "required_status_checks": [
          {
            "context": "GOVERDOCS Governance Gate",
            "integration_id": 15368
          }
        ],
        "strict_required_status_checks_policy": true
      }
    }
  ]
}
JSON

gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "repos/${REPO}/rulesets" \
  --input /tmp/goverdocs-r9-ruleset.json
```

Do not add bypass actors during activation.

## Verification

GitHub effective-rule API:

```bash
gh api \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/nulleimy/Goverdocs/rules/branches/main
```

GOVERDOCS verifier:

```bash
goverdocs-github-enforcement \
  --repository nulleimy/Goverdocs \
  --branch main
```

Expected exit code: `0`.

Expected status:

```json
{
  "status": "PASS",
  "required_context": "GOVERDOCS Governance Gate",
  "required_integration_id": 15368,
  "strict": true
}
```

Any missing rule, loose policy, wrong context, or unbound/wrong integration fails closed with exit code `2`.

## Enforcement proofs

### R9.2 — negative proof

Create an unmerged probe PR that intentionally causes `GOVERDOCS Governance Gate` to conclude non-success. GitHub must refuse the update/merge into `main` because the required check is not successful.

### R9.3 — positive proof

Create an unmerged docs-only probe that produces `GOVERDOCS Governance Gate — PASS`. GitHub must show the required rule as satisfied.

The probes are evidence only and must not alter canonical product behavior.

## Rollback

Read the repository rulesets and identify the exact R9 ruleset id:

```bash
gh api repos/nulleimy/Goverdocs/rulesets
```

Then delete only that ruleset:

```bash
gh api --method DELETE repos/nulleimy/Goverdocs/rulesets/<R9_RULESET_ID>
```

After rollback, `goverdocs-github-enforcement --repository nulleimy/Goverdocs` must return exit code `2` / `BLOCKED`, proving that hard enforcement is no longer active.
