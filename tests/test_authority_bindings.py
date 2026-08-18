from pathlib import Path

import pytest
import yaml

from goverdocs.authority_bindings import (
    AuthorityBindingError,
    active_role_bindings,
    load_authority_bindings,
)

ROLES = {"project-owner", "independent-reviewer"}


def _write_registry(tmp_path: Path, bindings: list[dict[str, object]]) -> Path:
    path = tmp_path / "AUTHORITY_BINDINGS.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "provider": "github",
                "recovery": {
                    "preserve_history": True,
                    "replacement_requires_new_binding_id": True,
                },
                "bindings": bindings,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def _binding(
    binding_id: str,
    login: str,
    role: str,
    *,
    status: str = "active",
    **extra: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "id": binding_id,
        "actor_id": f"github:{login}",
        "login": login,
        "role": role,
        "status": status,
        "enrolled_on": "2026-08-18",
        "evidence_refs": ["GH-ISSUE-53"],
    }
    value.update(extra)
    return value


def test_canonical_authority_bindings_are_active_and_deterministic() -> None:
    registry = load_authority_bindings(
        Path("policies/AUTHORITY_BINDINGS.yaml"),
        known_roles=ROLES,
    )

    assert active_role_bindings(registry) == {
        "nulleimy": "project-owner",
        "setarchitect": "independent-reviewer",
    }


def test_suspended_and_revoked_bindings_do_not_authorize(tmp_path: Path) -> None:
    path = _write_registry(
        tmp_path,
        [
            _binding("BIND-A", "active-user", "project-owner"),
            _binding(
                "BIND-B",
                "suspended-user",
                "independent-reviewer",
                status="suspended",
                suspended_on="2026-08-18",
                reason="temporary access hold",
            ),
            _binding(
                "BIND-C",
                "revoked-user",
                "independent-reviewer",
                status="revoked",
                revoked_on="2026-08-18",
                reason="authority withdrawn",
            ),
        ],
    )

    registry = load_authority_bindings(path, known_roles=ROLES)
    assert active_role_bindings(registry) == {"active-user": "project-owner"}


def test_duplicate_active_actor_fails_closed(tmp_path: Path) -> None:
    path = _write_registry(
        tmp_path,
        [
            _binding("BIND-A", "same-user", "project-owner"),
            _binding("BIND-B", "same-user", "independent-reviewer"),
        ],
    )

    with pytest.raises(AuthorityBindingError, match="multiple active bindings"):
        load_authority_bindings(path, known_roles=ROLES)


def test_duplicate_binding_id_fails_closed(tmp_path: Path) -> None:
    path = _write_registry(
        tmp_path,
        [
            _binding("BIND-A", "first-user", "project-owner"),
            _binding("BIND-A", "second-user", "independent-reviewer"),
        ],
    )

    with pytest.raises(AuthorityBindingError, match="duplicate authority binding id"):
        load_authority_bindings(path, known_roles=ROLES)


def test_unknown_role_fails_closed(tmp_path: Path) -> None:
    path = _write_registry(
        tmp_path,
        [_binding("BIND-A", "user", "unknown-role")],
    )

    with pytest.raises(AuthorityBindingError, match="unknown authority role"):
        load_authority_bindings(path, known_roles=ROLES)


def test_actor_id_must_match_github_login(tmp_path: Path) -> None:
    binding = _binding("BIND-A", "user", "project-owner")
    binding["actor_id"] = "github:someone-else"
    path = _write_registry(tmp_path, [binding])

    with pytest.raises(AuthorityBindingError, match="actor_id must equal"):
        load_authority_bindings(path, known_roles=ROLES)


def test_revoked_binding_requires_lifecycle_evidence(tmp_path: Path) -> None:
    path = _write_registry(
        tmp_path,
        [_binding("BIND-A", "user", "project-owner", status="revoked")],
    )

    with pytest.raises(AuthorityBindingError, match="revoked_on"):
        load_authority_bindings(path, known_roles=ROLES)
