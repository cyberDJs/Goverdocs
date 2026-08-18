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


def _github_user_id(value: object, *, field: str) -> int:
    actor_id = _non_empty_string(value, field=field)
    prefix = "github-user:"
    if not actor_id.startswith(prefix):
        raise AuthorityBindingError(f"{field} must use github-user:<numeric-id>")
    raw_id = actor_id[len(prefix) :]
    if not raw_id.isdigit() or raw_id.startswith("0"):
        raise AuthorityBindingError(f"{field} must use github-user:<numeric-id>")
    user_id = int(raw_id)
    if user_id < 1:
        raise AuthorityBindingError(f"{field} must use a positive GitHub user id")
    return user_id


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
    active_logins: dict[str, str] = {}
    active_actor_ids: dict[str, str] = {}
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
        github_user_id = _github_user_id(actor_id, field=f"{prefix}.actor_id")

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
            "github_user_id": github_user_id,
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
            if login in active_logins:
                previous_role = active_logins[login]
                raise AuthorityBindingError(
                    "authority login has multiple active bindings: "
                    f"{login} ({previous_role}, {role})"
                )
            if actor_id in active_actor_ids:
                previous_login = active_actor_ids[actor_id]
                raise AuthorityBindingError(
                    "immutable authority actor has multiple active aliases: "
                    f"{actor_id} ({previous_login}, {login})"
                )
            active_logins[login] = role
            active_actor_ids[actor_id] = login
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


def _active_bindings(registry: dict[str, Any]) -> list[dict[str, Any]]:
    raw_bindings = registry.get("bindings")
    if not isinstance(raw_bindings, list):
        raise AuthorityBindingError("normalized authority binding registry is invalid")
    active = [
        item
        for item in raw_bindings
        if isinstance(item, dict) and item.get("status") == "active"
    ]
    if not active:
        raise AuthorityBindingError("authority binding registry has no active bindings")
    return active


def active_role_bindings(registry: dict[str, Any]) -> dict[str, str]:
    active: dict[str, str] = {}
    for item in _active_bindings(registry):
        login = str(item.get("login") or "")
        role = str(item.get("role") or "")
        if not login or not role:
            raise AuthorityBindingError("active authority binding is missing login or role")
        if login in active:
            raise AuthorityBindingError(f"authority login has multiple active bindings: {login}")
        active[login] = role
    return dict(sorted(active.items()))


def active_github_user_id_bindings(registry: dict[str, Any]) -> dict[str, int]:
    active: dict[str, int] = {}
    seen_user_ids: dict[int, str] = {}
    for item in _active_bindings(registry):
        login = str(item.get("login") or "")
        raw_user_id = item.get("github_user_id")
        if not login or not isinstance(raw_user_id, int) or isinstance(raw_user_id, bool):
            raise AuthorityBindingError(
                "active authority binding is missing login or immutable GitHub user id"
            )
        if login in active:
            raise AuthorityBindingError(f"authority login has multiple active bindings: {login}")
        if raw_user_id in seen_user_ids:
            raise AuthorityBindingError(
                "immutable authority actor has multiple active aliases: "
                f"github-user:{raw_user_id} ({seen_user_ids[raw_user_id]}, {login})"
            )
        active[login] = raw_user_id
        seen_user_ids[raw_user_id] = login
    return dict(sorted(active.items()))
