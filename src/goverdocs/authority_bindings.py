from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml


class AuthorityBindingError(ValueError):
    pass


def _non_empty_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuthorityBindingError(f"{field} must be a non-empty string")
    return value.strip()


def _string_list(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise AuthorityBindingError(f"{field} must be a non-empty list")
    items = [_non_empty_string(item, field=field) for item in value]
    if len(items) != len(set(items)):
        raise AuthorityBindingError(f"{field} must not contain duplicates")
    return sorted(items)


def _iso_date(value: object, *, field: str) -> str:
    text = _non_empty_string(value, field=field)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise AuthorityBindingError(f"{field} must use YYYY-MM-DD") from exc
    return text


def load_authority_bindings(
    path: Path,
    *,
    known_roles: set[str],
) -> dict[str, Any]:
    if not path.exists():
        raise AuthorityBindingError(f"authority binding registry does not exist: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AuthorityBindingError("authority binding registry root must be a mapping")
    if raw.get("version") != 1:
        raise AuthorityBindingError("authority binding registry version must be 1")
    if raw.get("provider") != "github":
        raise AuthorityBindingError("authority binding registry provider must be github")

    recovery = raw.get("recovery")
    if not isinstance(recovery, dict):
        raise AuthorityBindingError("authority binding registry recovery must be a mapping")
    for field in ("preserve_history", "replacement_requires_new_binding_id"):
        if recovery.get(field) is not True:
            raise AuthorityBindingError(f"recovery.{field} must be true")

    raw_bindings = raw.get("bindings")
    if not isinstance(raw_bindings, list) or not raw_bindings:
        raise AuthorityBindingError("authority binding registry bindings must be a non-empty list")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    active_actor_roles: dict[str, str] = {}
    statuses = {"active", "suspended", "revoked"}

    for index, raw_binding in enumerate(raw_bindings):
        prefix = f"bindings[{index}]"
        if not isinstance(raw_binding, dict):
            raise AuthorityBindingError(f"{prefix} must be a mapping")

        binding_id = _non_empty_string(raw_binding.get("id"), field=f"{prefix}.id")
        if binding_id in seen_ids:
            raise AuthorityBindingError(f"duplicate authority binding id: {binding_id}")
        seen_ids.add(binding_id)

        login = _non_empty_string(raw_binding.get("login"), field=f"{prefix}.login")
        actor_id = _non_empty_string(raw_binding.get("actor_id"), field=f"{prefix}.actor_id")
        if actor_id != f"github:{login}":
            raise AuthorityBindingError(
                f"{prefix}.actor_id must equal github:<login> for the configured login"
            )

        role = _non_empty_string(raw_binding.get("role"), field=f"{prefix}.role")
        if role not in known_roles:
            raise AuthorityBindingError(
                f"{prefix}.role references unknown authority role: {role}"
            )

        status = _non_empty_string(raw_binding.get("status"), field=f"{prefix}.status")
        if status not in statuses:
            raise AuthorityBindingError(
                f"{prefix}.status must be one of: active, suspended, revoked"
            )

        enrolled_on = _iso_date(raw_binding.get("enrolled_on"), field=f"{prefix}.enrolled_on")
        evidence_refs = _string_list(
            raw_binding.get("evidence_refs"),
            field=f"{prefix}.evidence_refs",
        )

        normalized_binding: dict[str, Any] = {
            "id": binding_id,
            "actor_id": actor_id,
            "login": login,
            "role": role,
            "status": status,
            "enrolled_on": enrolled_on,
            "evidence_refs": evidence_refs,
        }

        if status == "active":
            if raw_binding.get("suspended_on") is not None or raw_binding.get("revoked_on") is not None:
                raise AuthorityBindingError(
                    f"{prefix} active binding must not declare suspended_on or revoked_on"
                )
            if login in active_actor_roles:
                previous_role = active_actor_roles[login]
                raise AuthorityBindingError(
                    "authority actor has multiple active bindings: "
                    f"{login} ({previous_role}, {role})"
                )
            active_actor_roles[login] = role
        elif status == "suspended":
            normalized_binding["suspended_on"] = _iso_date(
                raw_binding.get("suspended_on"),
                field=f"{prefix}.suspended_on",
            )
            normalized_binding["reason"] = _non_empty_string(
                raw_binding.get("reason"),
                field=f"{prefix}.reason",
            )
            if raw_binding.get("revoked_on") is not None:
                raise AuthorityBindingError(
                    f"{prefix} suspended binding must not declare revoked_on"
                )
        else:
            normalized_binding["revoked_on"] = _iso_date(
                raw_binding.get("revoked_on"),
                field=f"{prefix}.revoked_on",
            )
            normalized_binding["reason"] = _non_empty_string(
                raw_binding.get("reason"),
                field=f"{prefix}.reason",
            )

        normalized.append(normalized_binding)

    return {
        "version": 1,
        "provider": "github",
        "recovery": {
            "preserve_history": True,
            "replacement_requires_new_binding_id": True,
        },
        "bindings": sorted(normalized, key=lambda item: str(item["id"])),
    }


def active_role_bindings(registry: dict[str, Any]) -> dict[str, str]:
    raw_bindings = registry.get("bindings")
    if not isinstance(raw_bindings, list):
        raise AuthorityBindingError("normalized authority binding registry is invalid")

    active: dict[str, str] = {}
    for item in raw_bindings:
        if not isinstance(item, dict) or item.get("status") != "active":
            continue
        login = str(item.get("login") or "")
        role = str(item.get("role") or "")
        if not login or not role:
            raise AuthorityBindingError("active authority binding is missing login or role")
        if login in active:
            raise AuthorityBindingError(f"authority actor has multiple active bindings: {login}")
        active[login] = role
    if not active:
        raise AuthorityBindingError("authority binding registry has no active bindings")
    return dict(sorted(active.items()))
