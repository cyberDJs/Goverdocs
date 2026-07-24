from __future__ import annotations

import gzip
import hashlib
import importlib.util
import io
import tarfile
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
WORKFLOW = ROOT / ".github/workflows/quality.yml"
VERIFIER = ROOT / "scripts/verify_distribution.py"


def _configuration() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def test_pep_639_license_and_reproducible_build_backend() -> None:
    configuration = _configuration()

    assert configuration["build-system"]["requires"] == [
        "setuptools==83.0.0"
    ]
    assert configuration["project"]["license"] == "Apache-2.0"
    assert configuration["project"]["license-files"] == ["LICENSE"]

    classifiers = configuration["project"]["classifiers"]
    assert all(
        not classifier.startswith("License ::")
        for classifier in classifiers
    )


def test_runtime_dependencies_do_not_request_jsonschema_format_extra() -> None:
    dependencies = _configuration()["project"]["dependencies"]

    assert dependencies == [
        "PyYAML>=6.0.2,<7",
        "jsonschema>=4.23,<5",
    ]
    assert all("rfc3987" not in dependency.lower() for dependency in dependencies)
    assert all("jsonschema[" not in dependency.lower() for dependency in dependencies)


def test_release_tooling_is_explicitly_pinned() -> None:
    release_dependencies = _configuration()["project"][
        "optional-dependencies"
    ]["release"]

    assert release_dependencies == [
        "build==1.5.0",
        "twine==6.2.0",
    ]


def test_ci_contains_pinned_artifact_and_clean_install_gates() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd" in workflow
    assert "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405" in workflow
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow
    assert "python -m twine check --strict dist/*" in workflow
    assert "scripts/verify_distribution.py compare-sdist-payload" in workflow
    assert "scripts/verify_distribution.py canonicalize-sdist" in workflow
    assert "scripts/verify_distribution.py compare" in workflow
    assert "scripts/verify_distribution.py artifacts" in workflow
    assert "scripts/verify_distribution.py environment" in workflow
    assert "--only-binary=:all:" in workflow

    spec = importlib.util.spec_from_file_location(
        "verify_distribution",
        VERIFIER,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module._license_is_forbidden("GPL-3.0-only")
    assert module._license_is_forbidden(
        "GNU General Public License v3 (GPLv3)"
    )
    assert module._license_is_forbidden(
        "GNU Lesser General Public License v2 or later (LGPLv2+)"
    )
    assert not module._license_is_forbidden("Apache-2.0")
    assert not module._license_is_forbidden("MIT")

def _load_verifier_module():
    spec = importlib.util.spec_from_file_location(
        "verify_distribution_for_tests",
        VERIFIER,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_test_sdist(
    path: Path,
    *,
    gzip_mtime: int,
    tar_mtime: int,
    reverse_order: bool,
    unsafe_name: str | None = None,
) -> None:
    root_name = "goverdocs-0.1.0"
    file_name = unsafe_name or f"{root_name}/payload.txt"
    members = [
        ("directory", root_name, b""),
        ("file", file_name, b"deterministic payload\n"),
    ]
    if reverse_order:
        members.reverse()

    tar_buffer = io.BytesIO()
    with tarfile.open(
        fileobj=tar_buffer,
        mode="w",
        format=tarfile.PAX_FORMAT,
    ) as archive:
        for kind, name, data in members:
            member = tarfile.TarInfo(name=name)
            member.mtime = tar_mtime
            member.uid = tar_mtime % 1000
            member.gid = (tar_mtime + 1) % 1000
            member.uname = "builder"
            member.gname = "builder"
            if kind == "directory":
                member.type = tarfile.DIRTYPE
                member.mode = 0o755
                archive.addfile(member)
            else:
                member.type = tarfile.REGTYPE
                member.mode = 0o644
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))

    with (
        path.open("wb") as raw,
        gzip.GzipFile(
            filename=path.name,
            fileobj=raw,
            mode="wb",
            compresslevel=9,
            mtime=gzip_mtime,
        ) as compressed,
    ):
        compressed.write(tar_buffer.getvalue())


def test_sdist_canonicalization_is_reproducible_and_idempotent(
    tmp_path: Path,
) -> None:
    module = _load_verifier_module()
    left = tmp_path / "left.tar.gz"
    right = tmp_path / "right.tar.gz"
    epoch = 1_700_000_000

    _write_test_sdist(
        left,
        gzip_mtime=100,
        tar_mtime=200,
        reverse_order=False,
    )
    _write_test_sdist(
        right,
        gzip_mtime=300,
        tar_mtime=400,
        reverse_order=True,
    )

    assert left.read_bytes() != right.read_bytes()
    module.compare_sdist_payload(left, right)

    module.canonicalize_sdist(left, epoch)
    module.canonicalize_sdist(right, epoch)

    assert left.read_bytes() == right.read_bytes()
    first_hash = hashlib.sha256(left.read_bytes()).hexdigest()

    module.canonicalize_sdist(left, epoch)
    assert hashlib.sha256(left.read_bytes()).hexdigest() == first_hash

    with tarfile.open(left, mode="r:gz") as archive:
        for member in archive.getmembers():
            assert member.mtime == epoch
            assert member.uid == 0
            assert member.gid == 0
            assert member.uname == ""
            assert member.gname == ""


def test_sdist_canonicalization_rejects_path_traversal(
    tmp_path: Path,
) -> None:
    module = _load_verifier_module()
    unsafe = tmp_path / "unsafe.tar.gz"

    _write_test_sdist(
        unsafe,
        gzip_mtime=100,
        tar_mtime=200,
        reverse_order=False,
        unsafe_name="../escape.txt",
    )

    with pytest.raises(RuntimeError, match="unsafe sdist member path"):
        module.canonicalize_sdist(unsafe, 1_700_000_000)
