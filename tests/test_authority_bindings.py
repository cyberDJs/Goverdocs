from pathlib import Path

import pytest
import yaml

from goverdocs.authority_bindings import (
    AuthorityBindingError,
    active_identity_bindings,
    active_role_bindings,
    load_authority_bindings,
)

ROLES = {"project-owner", "independent-reviewer"}


def _event(
    event: str,
    on: str,
    *,
    refs: list[str] | None = None,
    reason: str | None = None,
) -> dict[str, object]:
    value: dict[str, object] = {
        "event": event,
        "on": on,
        "evidence_refs": refs or ["GH-ISSUE-64"],
    }
    if reason is not None:
        value["reason"] = reason
    return value


def _binding(
    binding_id: str,
    login: str,
    role: str,
    *,
    github_user_id: int = 100,
    origin: str = "initial",
    status: str = "active",
    enrolled_on: str = "2026-08-18",
    lifecycle: list[dict[str, object]] | None = None,
    replaces: str | None = None,
    replaced_by: str | None = None,
) -> dict[str, object]:
    refs = ["GH-ISSUE-64"]
    if lifecycle is None:
        lifecycle = [_event("enrolled", enrolled_on, refs=refs)]
        if status == "suspended":
            lifecycle.append(
                _event(
                    "suspended",
                    enrolled_on,
                    reason="temporary authority hold",
                )
            )
        elif status == "revoked":
            lifecycle.append(
                _event(
                    "revoked",
                    enrolled_on,
                    reason="authority withdrawn",
                )
            )
    value: dict[str, object] = {
        "id": binding_id,
        "actor_id": f"github-user:{github_user_id}",
        "login": login,
        "role": role,
        "origin": origin,
        "status": status,
        "enrolled_on": enrolled_on,
        "evidence_refs": refs,
        "lifecycle": lifecycle,
    }
    if replaces is not None:
        value["replaces"] = replaces
    if replaced_by is not None:
        value["replaced_by"] = replaced_by
    return value


def _write_registry(
    tmp_path: Path,
    bindings: list[dict[str, object]],
    *,
    initial_binding_ids: list[str] | None = None,
) -> Path:
    if initial_binding_ids is None:
        initial_binding_ids = sorted(
            {
                str(item["id"])
                for item in bindings
                if item.get("origin") == "initial"
            }
        )
    path = tmp_path / "AUTHORITY_BINDINGS.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 2,
                "provider": "github",
                "recovery": {
                    "preserve_history": True,
                    "replacement_requires_new_binding_id": True,
                    "explicit_lifecycle_required": True,
                    "revoked_bindings_terminal": True,
                    "initial_enrollment_closed_on": "2026-08-18",
                    "initial_binding_ids": initial_binding_ids,
                },
                "bindings": bindings,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def test_canonical_authority_bindings_are_active_and_deterministic() -> None:
    registry = load_authority_bindings(
        Path("policies/AUTHORITY_BINDINGS.yaml"),
        known_roles=ROLES,
    )

    assert registry["version"] == 2
    assert active_role_bindings(registry) == {
        "nulleimy": "project-owner",
        "setarchitect": "independent-reviewer",
    }
    assert active_identity_bindings(registry) == {
        "nulleimy": {
            "actor_id": "github-user:268458602",
            "role": "project-owner",
        },
        "setarchitect": {
            "actor_id": "github-user:264658998",
            "role": "independent-reviewer",
        },
    }


def test_suspended_and_revoked_bindings_do_not_authorize(tmp_path: Path) -> None:
    path = _write_registry(
        tmp_path,
        [
            _binding("BIND-A", "active-user", "project-owner", github_user_id=101),
            _binding(
                "BIND-B",
                "suspended-user",
                "independent-reviewer",
                github_user_id=102,
                status="suspended",
            ),
            _binding(
                "BIND-C",
                "revoked-user",
                "independent-reviewer",
                github_user_id=103,
                status="revoked",
            ),
        ],
    )

    registry = load_authority_bindings(path, known_roles=ROLES)
    assert active_role_bindings(registry) == {"active-user": "project-owner"}


def test_duplicate_active_login_fails_closed(tmp_path: Path) -> None:
    path = _write_registry(
        tmp_path,
        [
            _binding("BIND-A", "same-user", "project-owner", github_user_id=101),
            _binding(
                "BIND-B",
                "same-user",
                "independent-reviewer",
                github_user_id=102,
            ),
        ],
    )

    with pytest.raises(AuthorityBindingError, match="login has multiple active bindings"):
        load_authority_bindings(path, known_roles=ROLES)


def test_duplicate_active_immutable_actor_fails_closed(tmp_path: Path) -> None:
    path = _write_registry(
        tmp_path,
        [
            _binding("BIND-A", "first-alias", "project-owner", github_user_id=101),
            _binding(
                "BIND-B",
                "second-alias",
                "independent-reviewer",
                github_user_id=101,
            ),
        ],
    )

    with pytest.raises(AuthorityBindingError, match="immutable authority actor"):
        load_authority_bindings(path, known_roles=ROLES)


def test_duplicate_binding_id_fails_closed(tmp_path: Path) -> None:
    path = _write_registry(
        tmp_path,
        [
            _binding("BIND-A", "first-user", "project-owner", github_user_id=101),
            _binding(
                "BIND-A",
                "second-user",
                "independent-reviewer",
                github_user_id=102,
            ),
        ],
    )

    with pytest.raises(AuthorityBindingError, match="duplicate authority binding id"):
        load_authority_bindings(path, known_roles=ROLES)


def test_unknown_role_fails_closed(tmp_path: Path) -> None:
    path = _write_registry(
        tmp_path,
        [_binding("BIND-A", "user", "unknown-role", github_user_id=101)],
    )

    with pytest.raises(AuthorityBindingError, match="unknown authority role"):
        load_authority_bindings(path, known_roles=ROLES)


def test_actor_id_must_be_immutable_numeric_github_id(tmp_path: Path) -> None:
    binding = _binding("BIND-A", "user", "project-owner", github_user_id=101)
    binding["actor_id"] = "github:user"
    path = _write_registry(tmp_path, [binding])

    with pytest.raises(AuthorityBindingError, match="github-user:<numeric-id>"):
        load_authority_bindings(path, known_roles=ROLES)


def test_status_only_mutation_cannot_reactivate_suspended_binding(tmp_path: Path) -> None:
    lifecycle = [
        _event("enrolled", "2026-08-18"),
        _event("suspended", "2026-08-18", reason="incident hold"),
    ]
    path = _write_registry(
        tmp_path,
        [
            _binding(
                "BIND-A",
                "user",
                "project-owner",
                github_user_id=101,
                status="active",
                lifecycle=lifecycle,
            )
        ],
    )

    with pytest.raises(AuthorityBindingError, match="lifecycle-derived state suspended"):
        load_authority_bindings(path, known_roles=ROLES)


def test_explicit_suspend_resume_history_can_restore_active_state(tmp_path: Path) -> None:
    lifecycle = [
        _event("enrolled", "2026-08-18"),
        _event("suspended", "2026-08-18", reason="incident hold"),
        _event("resumed", "2026-08-18", reason="recovery evidence accepted"),
    ]
    path = _write_registry(
        tmp_path,
        [
            _binding(
                "BIND-A",
                "user",
                "project-owner",
                github_user_id=101,
                lifecycle=lifecycle,
            )
        ],
    )

    registry = load_authority_bindings(path, known_roles=ROLES)
    assert active_role_bindings(registry) == {"user": "project-owner"}


def test_revoked_state_is_terminal(tmp_path: Path) -> None:
    lifecycle = [
        _event("enrolled", "2026-08-18"),
        _event("revoked", "2026-08-18", reason="identity retired"),
        _event("resumed", "2026-08-18", reason="invalid reactivation"),
    ]
    path = _write_registry(
        tmp_path,
        [
            _binding(
                "BIND-A",
                "user",
                "project-owner",
                github_user_id=101,
                lifecycle=lifecycle,
            )
        ],
    )

    with pytest.raises(AuthorityBindingError, match="terminal revoked state"):
        load_authority_bindings(path, known_roles=ROLES)


def test_valid_replacement_authorizes_only_new_identity(tmp_path: Path) -> None:
    old = _binding(
        "BIND-OLD",
        "old-user",
        "project-owner",
        github_user_id=101,
        status="revoked",
        replaced_by="BIND-NEW",
    )
    new = _binding(
        "BIND-NEW",
        "new-user",
        "project-owner",
        github_user_id=202,
        origin="replacement",
        enrolled_on="2026-08-18",
        replaces="BIND-OLD",
    )
    path = _write_registry(tmp_path, [old, new])

    registry = load_authority_bindings(path, known_roles=ROLES)
    assert active_identity_bindings(registry) == {
        "new-user": {
            "actor_id": "github-user:202",
            "role": "project-owner",
        }
    }


def test_replacement_requires_revoked_predecessor(tmp_path: Path) -> None:
    old = _binding(
        "BIND-OLD",
        "old-user",
        "project-owner",
        github_user_id=101,
        replaced_by="BIND-NEW",
    )
    new = _binding(
        "BIND-NEW",
        "new-user",
        "project-owner",
        github_user_id=202,
        origin="replacement",
        replaces="BIND-OLD",
    )
    path = _write_registry(tmp_path, [old, new])

    with pytest.raises(AuthorityBindingError, match="predecessor must be revoked"):
        load_authority_bindings(path, known_roles=ROLES)


def test_replacement_requires_predecessor_backlink(tmp_path: Path) -> None:
    old = _binding(
        "BIND-OLD",
        "old-user",
        "project-owner",
        github_user_id=101,
        status="revoked",
    )
    new = _binding(
        "BIND-NEW",
        "new-user",
        "project-owner",
        github_user_id=202,
        origin="replacement",
        replaces="BIND-OLD",
    )
    path = _write_registry(tmp_path, [old, new])

    with pytest.raises(AuthorityBindingError, match="point back via replaced_by"):
        load_authority_bindings(path, known_roles=ROLES)


def test_replacement_must_preserve_role(tmp_path: Path) -> None:
    old = _binding(
        "BIND-OLD",
        "old-user",
        "project-owner",
        github_user_id=101,
        status="revoked",
        replaced_by="BIND-NEW",
    )
    new = _binding(
        "BIND-NEW",
        "new-user",
        "independent-reviewer",
        github_user_id=202,
        origin="replacement",
        replaces="BIND-OLD",
    )
    path = _write_registry(tmp_path, [old, new])

    with pytest.raises(AuthorityBindingError, match="preserve predecessor role"):
        load_authority_bindings(path, known_roles=ROLES)


def test_replacement_must_change_immutable_actor(tmp_path: Path) -> None:
    old = _binding(
        "BIND-OLD",
        "old-user",
        "project-owner",
        github_user_id=101,
        status="revoked",
        replaced_by="BIND-NEW",
    )
    new = _binding(
        "BIND-NEW",
        "new-user",
        "project-owner",
        github_user_id=101,
        origin="replacement",
        replaces="BIND-OLD",
    )
    path = _write_registry(tmp_path, [old, new])

    with pytest.raises(AuthorityBindingError, match="different immutable actor id"):
        load_authority_bindings(path, known_roles=ROLES)


def test_replacement_enrollment_cannot_precede_revocation(tmp_path: Path) -> None:
    old_lifecycle = [
        _event("enrolled", "2026-08-18"),
        _event("revoked", "2026-08-19", reason="identity retired"),
    ]
    old = _binding(
        "BIND-OLD",
        "old-user",
        "project-owner",
        github_user_id=101,
        status="revoked",
        lifecycle=old_lifecycle,
        replaced_by="BIND-NEW",
    )
    new = _binding(
        "BIND-NEW",
        "new-user",
        "project-owner",
        github_user_id=202,
        origin="replacement",
        enrolled_on="2026-08-18",
        replaces="BIND-OLD",
    )
    path = _write_registry(tmp_path, [old, new])

    with pytest.raises(AuthorityBindingError, match="precedes predecessor revocation"):
        load_authority_bindings(path, known_roles=ROLES)


def test_replacement_chain_cannot_branch(tmp_path: Path) -> None:
    old = _binding(
        "BIND-OLD",
        "old-user",
        "project-owner",
        github_user_id=101,
        status="revoked",
        replaced_by="BIND-NEW-A",
    )
    first = _binding(
        "BIND-NEW-A",
        "new-a",
        "project-owner",
        github_user_id=202,
        origin="replacement",
        replaces="BIND-OLD",
    )
    second = _binding(
        "BIND-NEW-B",
        "new-b",
        "project-owner",
        github_user_id=303,
        origin="replacement",
        replaces="BIND-OLD",
    )
    path = _write_registry(tmp_path, [old, first, second])

    with pytest.raises(AuthorityBindingError, match="replacement chain branches"):
        load_authority_bindings(path, known_roles=ROLES)


def test_replacement_chain_cannot_cycle(tmp_path: Path) -> None:
    root = _binding(
        "BIND-ROOT",
        "root",
        "independent-reviewer",
        github_user_id=999,
    )
    first = _binding(
        "BIND-A",
        "user-a",
        "project-owner",
        github_user_id=101,
        origin="replacement",
        status="revoked",
        replaces="BIND-B",
        replaced_by="BIND-B",
    )
    second = _binding(
        "BIND-B",
        "user-b",
        "project-owner",
        github_user_id=202,
        origin="replacement",
        status="revoked",
        replaces="BIND-A",
        replaced_by="BIND-A",
    )
    path = _write_registry(tmp_path, [root, first, second])

    with pytest.raises(AuthorityBindingError, match="contains a cycle"):
        load_authority_bindings(path, known_roles=ROLES)


def test_new_initial_binding_after_enrollment_lock_fails_closed(tmp_path: Path) -> None:
    late = _binding(
        "BIND-LATE",
        "late-user",
        "project-owner",
        github_user_id=101,
        enrolled_on="2026-08-19",
    )
    path = _write_registry(tmp_path, [late])

    with pytest.raises(AuthorityBindingError, match="initial enrollment occurs after"):
        load_authority_bindings(path, known_roles=ROLES)
