from __future__ import annotations

import hashlib
import json
from datetime import date
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


def change_digest(changed_files: list[str], diff_text: str) -> str:
    payload = {"changed_files": sorted(changed_files), "diff_text": diff_text}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def record_digest(record: dict[str, Any]) -> str:
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json_records(paths: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        value = json.loads(path.read_text(encoding="utf-8"))
        values = value if isinstance(value, list) else [value]
        for item in values:
            if not isinstance(item, dict):
                raise ValueError(f"JSON evidence record must be an object: {path}")
            records.append(item)
    return records


def validate_record(record: dict[str, Any], schema_name: str) -> list[str]:
    schema_path = resources.files("goverdocs").joinpath(f"resources/{schema_name}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return sorted(error.message for error in validator.iter_errors(record))


def verification_is_trusted(record: dict[str, Any], trusted_verifiers: set[str]) -> tuple[bool, str]:
    verification = record.get("verification")
    if not isinstance(verification, dict):
        return False, "verification object is missing"
    if verification.get("status") != "verified":
        return False, f"verification status is {verification.get('status', 'missing')}"
    verifier_id = str(verification.get("verifier_id") or "")
    if not verifier_id:
        return False, "verifier_id is missing"
    if verifier_id not in trusted_verifiers:
        return False, f"verifier {verifier_id} is not trusted for this evaluation"
    return True, f"verified by trusted verifier {verifier_id}"


def verification_is_fresh(record: dict[str, Any], as_of: date) -> tuple[bool, str]:
    verification = record.get("verification")
    if not isinstance(verification, dict):
        return False, "verification object is missing"
    raw_valid_until = verification.get("valid_until")
    if raw_valid_until is None:
        return True, "verification has no expiry"
    if not isinstance(raw_valid_until, str):
        return False, "valid_until is not an ISO date string"
    try:
        valid_until = date.fromisoformat(raw_valid_until)
    except ValueError:
        return False, "valid_until is not a valid ISO date"
    if valid_until < as_of:
        return False, f"verification expired on {valid_until.isoformat()}"
    return True, f"verification valid through {valid_until.isoformat()}"


def subject_matches(
    record: dict[str, Any],
    *,
    expected_change_digest: str,
    repository: str | None,
    pull_request: int | None,
    head_sha: str | None,
    require_scm_context: bool,
) -> tuple[bool, str]:
    subject = record.get("subject")
    if not isinstance(subject, dict):
        return False, "subject object is missing"
    if subject.get("change_digest") != expected_change_digest:
        return False, "change_digest does not match the evaluated change"

    if require_scm_context and (repository is None or pull_request is None or head_sha is None):
        return False, "repository, pull_request and head_sha evaluation context are required"

    comparisons = (
        ("repository", repository),
        ("pull_request", pull_request),
        ("head_sha", head_sha),
    )
    for key, expected in comparisons:
        actual = subject.get(key)
        if actual is None:
            if require_scm_context:
                return False, f"subject.{key} is required"
            continue
        if expected is None:
            return False, f"subject.{key} is bound but evaluation context does not provide it"
        if actual != expected:
            return False, f"subject.{key} does not match the evaluation context"
    return True, "subject binding matches the evaluated change"
