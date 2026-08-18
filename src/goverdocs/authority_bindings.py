from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml


class AuthorityBindingError(ValueError):
    pass


_GITHUB_USER_ACTOR_ID = re.compile(r"^github-user:([1-9][0-9]*)$")
_STATUSES = {"active", "suspended", "revoked"}
_EVENTS = {"enrolled", "suspended", "resumed", "revoked"}
_ORIGINS = {"initial", "replacement"}


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


def _normalize_lifecycle(
    value: object,
    *,
    prefix: str,
    enrolled_on: str,
    enrollment_evidence_refs: list[str],
) -> tuple[list[dict[str, Any]], str, str | None]:
    if not isinstance(value, list) or not value:
        raise AuthorityBindingError(f"{prefix}.lifecycle must be a non-empty list")

    normalized: list[dict[str, Any]] = []
    state: str | None = None
    previous_on: str | None = None
    revoked_on: str | None = None

    for index, raw_event in enumerate(value):
        event_prefix = f"{prefix}.lifecycle[{index}]"
        if not isinstance(raw_event, dict):
            raise AuthorityBindingError(f"{event_prefix} must be a mapping")

        event = _non_empty_string(raw_event.get("event"), field=f"{event_prefix}.event")
        if event not in _EVENTS:
            raise AuthorityBindingError(
                f"{event_prefix}.event must be one of: enrolled, suspended, resumed, revoked"
            )
        event_on = _iso_date(raw_event.get("on"), field=f"{event_prefix}.on")
        evidence_refs = _string_list(
            raw_event.get("evidence_refs"),
            field=f"{event_prefix}.evidence_refs",
        )
        if previous_on is not None and event_on < previous_on:
            raise AuthorityBindingError(
                f"{event_prefix}.on must not precede the previous lifecycle event"
            )
        previous_on = event_on

        item: dict[str, Any] = {
            "event": event,
            "on": event_on,
            "evidence_refs": evidence_refs,
        }

        if index == 0:
            if event != "enrolled":
                raise AuthorityBindingError(f"{prefix}.lifecycle must begin with enrolled")
            if event_on != enrolled_on:
                raise AuthorityBindingError(
                    f"{event_prefix}.on must equal {prefix}.enrolled_on"
                )
            if evidence_refs != enrollment_evidence_refs:
                raise AuthorityBindingError(
                    f"{event_prefix}.evidence_refs must equal {prefix}.evidence_refs"
                )
            state = "active"
        else:
            if state == "revoked":
                raise AuthorityBindingError(
                    f"{event_prefix} follows terminal revoked state"
                )
            if event == "enrolled":
                raise AuthorityBindingError(
                    f"{event_prefix}.event cannot enroll an existing binding again"
                )
            if event == "suspended":
                if state != "active":
                    raise AuthorityBindingError(
                        f"{event_prefix}.event requires active predecessor state"
                    )
                state = "suspended"
            elif event == "resumed":
                if state != "suspended":
                    raise AuthorityBindingError(
                        f"{event_prefix}.event requires suspended predecessor state"
                    )
                state = "active"
            else:
                if state not in {"active", "suspended"}:
                    raise AuthorityBindingError(
                        f"{event_prefix}.event requires active or suspended predecessor state"
                    )
                state = "revoked"
                revoked_on = event_on

            item["reason"] = _non_empty_string(
                raw_event.get("reason"),
                field=f"{event_prefix}.reason",
            )

        normalized.append(item)

    assert state is not None
    return normalized, state, revoked_on


def _validate_replacement_graph(bindings: list[dict[str, Any]]) -> None:
    by_id = {str(item["id"]): item for item in bindings}
    predecessor_use: dict[str, str] = {}

    for item in bindings:
        binding_id = str(item["id"])
        origin = str(item["origin"])
        replaces = item.get("replaces")
        replaced_by = item.get("replaced_by")

        if origin == "initial":
            if replaces is not None:
                raise AuthorityBindingError(
                    f"{binding_id} initial binding must not declare replaces"
                )
        else:
            predecessor_id = str(replaces or "")
            if not predecessor_id:
                raise AuthorityBindingError(
                    f"{binding_id} replacement binding must declare replaces"
                )
            predecessor = by_id.get(predecessor_id)
            if predecessor is None:
                raise AuthorityBindingError(
                    f"{binding_id} replacement predecessor does not exist: {predecessor_id}"
                )
            previous_successor = predecessor_use.get(predecessor_id)
            if previous_successor is not None:
                raise AuthorityBindingError(
                    "authority replacement chain branches from predecessor "
                    f"{predecessor_id}: {previous_successor}, {binding_id}"
                )
            predecessor_use[predecessor_id] = binding_id

            if predecessor.get("status") != "revoked":
                raise AuthorityBindingError(
                    f"{binding_id} replacement predecessor must be revoked: {predecessor_id}"
                )
            if predecessor.get("replaced_by") != binding_id:
                raise AuthorityBindingError(
                    f"{binding_id} replacement predecessor must point back via replaced_by"
                )
            if predecessor.get("role") != item.get("role"):
                raise AuthorityBindingError(
                    f"{binding_id} replacement must preserve predecessor role"
                )
            if predecessor.get("actor_id") == item.get("actor_id"):
                raise AuthorityBindingError(
                    f"{binding_id} replacement must use a different immutable actor id"
                )
            predecessor_revoked_on = predecessor.get("_revoked_on")
            if not isinstance(predecessor_revoked_on, str):
                raise AuthorityBindingError(
                    f"{binding_id} replacement predecessor is missing revoked lifecycle state"
                )
            if str(item["enrolled_on"]) < predecessor_revoked_on:
                raise AuthorityBindingError(
                    f"{binding_id} replacement enrollment precedes predecessor revocation"
                )

        if replaced_by is not None:
            if item.get("status") != "revoked":
                raise AuthorityBindingError(
                    f"{binding_id} replaced_by is allowed only on revoked bindings"
                )
            successor_id = str(replaced_by)
            successor = by_id.get(successor_id)
            if successor is None:
                raise AuthorityBindingError(
                    f"{binding_id} replaced_by target does not exist: {successor_id}"
                )
            if successor.get("origin") != "replacement" or successor.get("replaces") != binding_id:
                raise AuthorityBindingError(
                    f"{binding_id} replaced_by target must point back through replaces"
                )

    for item in bindings:
        start = str(item["id"])
        seen: set[str] = set()
        current = item
        while current.get("origin") == "replacement":
            current_id = str(current["id"])
            if current_id in seen:
                raise AuthorityBindingError(
                    f"authority replacement chain contains a cycle at {current_id}"
                )
            seen.add(current_id)
            predecessor_id = str(current.get("replaces") or "")
            if predecessor_id == start or predecessor_id in seen:
                raise AuthorityBindingError(
                    f"authority replacement chain contains a cycle at {predecessor_id}"
                )
            predecessor = by_id.get(predecessor_id)
            if predecessor is None:
                break
            current = predecessor


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
    if raw.get("version") != 2:
        raise AuthorityBindingError("authority binding registry version must be 2")
    if raw.get("provider") != "github":
        raise AuthorityBindingError("authority binding registry provider must be github")

    recovery = raw.get("recovery")
    if not isinstance(recovery, dict):
        raise AuthorityBindingError("authority binding registry recovery must be a mapping")
    for field in (
        "preserve_history",
        "replacement_requires_new_binding_id",
        "explicit_lifecycle_required",
        "revoked_bindings_terminal",
    ):
        if recovery.get(field) is not True:
            raise AuthorityBindingError(f"recovery.{field} must be true")
    initial_enrollment_closed_on = _iso_date(
        recovery.get("initial_enrollment_closed_on"),
        field="recovery.initial_enrollment_closed_on",
    )
    initial_binding_ids = _string_list(
        recovery.get("initial_binding_ids"),
        field="recovery.initial_binding_ids",
    )

    raw_bindings = raw.get("bindings")
    if not isinstance(raw_bindings, list) or not raw_bindings:
        raise AuthorityBindingError("authority binding registry bindings must be a non-empty list")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    active_logins: dict[str, str] = {}
    active_actor_ids: dict[str, str] = {}
    observed_initial_ids: set[str] = set()

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
        if _GITHUB_USER_ACTOR_ID.fullmatch(actor_id) is None:
            raise AuthorityBindingError(
                f"{prefix}.actor_id must use immutable github-user:<numeric-id> format"
            )

        role = _non_empty_string(raw_binding.get("role"), field=f"{prefix}.role")
        if role not in known_roles:
            raise AuthorityBindingError(
                f"{prefix}.role references unknown authority role: {role}"
            )

        origin = _non_empty_string(raw_binding.get("origin"), field=f"{prefix}.origin")
        if origin not in _ORIGINS:
            raise AuthorityBindingError(
                f"{prefix}.origin must be one of: initial, replacement"
            )

        status = _non_empty_string(raw_binding.get("status"), field=f"{prefix}.status")
        if status not in _STATUSES:
            raise AuthorityBindingError(
                f"{prefix}.status must be one of: active, suspended, revoked"
            )

        enrolled_on = _iso_date(raw_binding.get("enrolled_on"), field=f"{prefix}.enrolled_on")
        evidence_refs = _string_list(
            raw_binding.get("evidence_refs"),
            field=f"{prefix}.evidence_refs",
        )
        lifecycle, derived_status, revoked_on = _normalize_lifecycle(
            raw_binding.get("lifecycle"),
            prefix=prefix,
            enrolled_on=enrolled_on,
            enrollment_evidence_refs=evidence_refs,
        )
        if status != derived_status:
            raise AuthorityBindingError(
                f"{prefix}.status does not match lifecycle-derived state {derived_status}"
            )

        normalized_binding: dict[str, Any] = {
            "id": binding_id,
            "actor_id": actor_id,
            "login": login,
            "role": role,
            "origin": origin,
            "status": status,
            "enrolled_on": enrolled_on,
            "evidence_refs": evidence_refs,
            "lifecycle": lifecycle,
            "_revoked_on": revoked_on,
        }

        if origin == "initial":
            observed_initial_ids.add(binding_id)
            if binding_id not in initial_binding_ids:
                raise AuthorityBindingError(
                    f"{prefix} initial binding id is not declared in recovery.initial_binding_ids"
                )
            if enrolled_on > initial_enrollment_closed_on:
                raise AuthorityBindingError(
                    f"{prefix} initial enrollment occurs after recovery.initial_enrollment_closed_on"
                )
            if raw_binding.get("replaces") is not None:
                raise AuthorityBindingError(
                    f"{prefix} initial binding must not declare replaces"
                )
        else:
            normalized_binding["replaces"] = _non_empty_string(
                raw_binding.get("replaces"),
                field=f"{prefix}.replaces",
            )

        if raw_binding.get("replaced_by") is not None:
            normalized_binding["replaced_by"] = _non_empty_string(
                raw_binding.get("replaced_by"),
                field=f"{prefix}.replaced_by",
            )

        if status == "active":
            if login in active_logins:
                previous_role = active_logins[login]
                raise AuthorityBindingError(
                    "authority login has multiple active bindings: "
                    f"{login} ({previous_role}, {role})"
                )
            if actor_id in active_actor_ids:
                previous_login = active_actor_ids[actor_id]
                raise AuthorityBindingError(
                    "immutable authority actor has multiple active bindings: "
                    f"{actor_id} ({previous_login}, {login})"
                )
            active_logins[login] = role
            active_actor_ids[actor_id] = login

        normalized.append(normalized_binding)

    if observed_initial_ids != set(initial_binding_ids):
        missing = sorted(set(initial_binding_ids) - observed_initial_ids)
        extra = sorted(observed_initial_ids - set(initial_binding_ids))
        details: list[str] = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if extra:
            details.append("extra=" + ",".join(extra))
        raise AuthorityBindingError(
            "recovery.initial_binding_ids must exactly match initial bindings"
            + (": " + "; ".join(details) if details else "")
        )

    _validate_replacement_graph(normalized)

    clean_bindings: list[dict[str, Any]] = []
    for item in normalized:
        clean_bindings.append(
            {key: value for key, value in item.items() if not key.startswith("_")}
        )

    return {
        "version": 2,
        "provider": "github",
        "recovery": {
            "preserve_history": True,
            "replacement_requires_new_binding_id": True,
            "explicit_lifecycle_required": True,
            "revoked_bindings_terminal": True,
            "initial_enrollment_closed_on": initial_enrollment_closed_on,
            "initial_binding_ids": initial_binding_ids,
        },
        "bindings": sorted(clean_bindings, key=lambda item: str(item["id"])),
    }


def active_identity_bindings(registry: dict[str, Any]) -> dict[str, dict[str, str]]:
    raw_bindings = registry.get("bindings")
    if not isinstance(raw_bindings, list):
        raise AuthorityBindingError("normalized authority binding registry is invalid")

    active: dict[str, dict[str, str]] = {}
    actor_ids: set[str] = set()
    for item in raw_bindings:
        if not isinstance(item, dict) or item.get("status") != "active":
            continue
        login = str(item.get("login") or "")
        role = str(item.get("role") or "")
        actor_id = str(item.get("actor_id") or "")
        if not login or not role or not actor_id:
            raise AuthorityBindingError(
                "active authority binding is missing login, role or actor_id"
            )
        if login in active:
            raise AuthorityBindingError(f"authority login has multiple active bindings: {login}")
        if actor_id in actor_ids:
            raise AuthorityBindingError(
                f"immutable authority actor has multiple active bindings: {actor_id}"
            )
        actor_ids.add(actor_id)
        active[login] = {"actor_id": actor_id, "role": role}
    if not active:
        raise AuthorityBindingError("authority binding registry has no active bindings")
    return dict(sorted(active.items()))


def active_role_bindings(registry: dict[str, Any]) -> dict[str, str]:
    return {
        login: binding["role"]
        for login, binding in active_identity_bindings(registry).items()
    }
