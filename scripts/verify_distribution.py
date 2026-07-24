from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import tomllib
import zipfile
from collections import deque
from email.parser import BytesParser
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = ROOT / "pyproject.toml"
LICENSE_PATH = ROOT / "LICENSE"
FORBIDDEN_RUNTIME_DISTRIBUTIONS = {"rfc3987"}
FORBIDDEN_LICENSE_MARKERS = (
    "AGPL-",
    "GPL-",
    "LGPL-",
    "AGPLV",
    "GPLV",
    "LGPLV",
    "GNU AFFERO GENERAL PUBLIC LICENSE",
    "GNU GENERAL PUBLIC LICENSE",
    "GNU LESSER GENERAL PUBLIC LICENSE",
)
REQUIREMENT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")


def _canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _project_metadata() -> dict[str, Any]:
    payload = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    project = payload.get("project")
    if not isinstance(project, dict):
        raise RuntimeError("pyproject.toml is missing [project]")
    return project


def _requirement_name(requirement: str) -> str:
    match = REQUIREMENT_NAME.match(requirement.strip())
    if match is None:
        raise RuntimeError(f"cannot parse requirement name: {requirement}")
    return _canonical_name(match.group(0))


def _is_optional_requirement(requirement: str) -> bool:
    return "extra ==" in requirement.lower()


def _git_output(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _source_state() -> tuple[str, bool]:
    commit = _git_output("rev-parse", "HEAD")
    dirty = bool(_git_output("status", "--porcelain"))
    github_sha = os.environ.get("GITHUB_SHA")

    if github_sha and github_sha != commit:
        raise RuntimeError(
            f"GITHUB_SHA {github_sha} does not match checked-out commit {commit}"
        )
    if os.environ.get("GITHUB_ACTIONS") == "true" and dirty:
        raise RuntimeError("GitHub Actions release build has a dirty worktree")

    return commit, dirty


def _single_artifact(dist_dir: Path, pattern: str) -> Path:
    matches = sorted(dist_dir.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {pattern}, found {matches}")
    return matches[0]


def verify_artifacts(dist_dir: Path, manifest_path: Path) -> None:
    project = _project_metadata()
    project_name = str(project["name"])
    version = str(project["version"])
    license_expression = str(project["license"])
    license_files = project.get("license-files")

    if license_expression != "Apache-2.0":
        raise RuntimeError(f"unexpected project license: {license_expression}")
    if license_files != ["LICENSE"]:
        raise RuntimeError(f"unexpected license-files: {license_files}")

    normalized_name = _canonical_name(project_name).replace("-", "_")
    sdist = _single_artifact(dist_dir, f"{normalized_name}-{version}.tar.gz")
    wheel = _single_artifact(dist_dir, f"{normalized_name}-{version}-py3-none-any.whl")
    root_license = LICENSE_PATH.read_bytes()

    with tarfile.open(sdist, "r:gz") as archive:
        regular_files = {
            member.name: member
            for member in archive.getmembers()
            if member.isfile()
        }
        prefix = f"{normalized_name}-{version}/"
        required = {
            prefix + "LICENSE",
            prefix + "README.md",
            prefix + "pyproject.toml",
            prefix + "src/goverdocs/__init__.py",
            prefix + "src/goverdocs/cli.py",
                    }
        missing = sorted(required - regular_files.keys())
        if missing:
            raise RuntimeError(f"sdist is missing required files: {missing}")

        license_member = archive.extractfile(regular_files[prefix + "LICENSE"])
        if license_member is None or license_member.read() != root_license:
            raise RuntimeError("sdist LICENSE does not match repository LICENSE")

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata_paths = sorted(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        if len(metadata_paths) != 1:
            raise RuntimeError(f"unexpected wheel metadata paths: {metadata_paths}")

        message = BytesParser().parsebytes(archive.read(metadata_paths[0]))
        if _canonical_name(str(message["Name"])) != _canonical_name(project_name):
            raise RuntimeError(f"unexpected wheel Name: {message['Name']}")
        if message["Version"] != version:
            raise RuntimeError(f"unexpected wheel Version: {message['Version']}")
        if message["License-Expression"] != license_expression:
            raise RuntimeError(
                "wheel License-Expression does not match pyproject.toml"
            )
        if message["Requires-Python"] != project["requires-python"]:
            raise RuntimeError("wheel Requires-Python does not match pyproject.toml")

        metadata_license_files = message.get_all("License-File", [])
        if not any(Path(value).name == "LICENSE" for value in metadata_license_files):
            raise RuntimeError(
                f"wheel metadata does not declare LICENSE: {metadata_license_files}"
            )

        requirements = message.get_all("Requires-Dist", [])
        base_requirements = [
            requirement
            for requirement in requirements
            if not _is_optional_requirement(requirement)
        ]
        base_names = {_requirement_name(value) for value in base_requirements}
        if base_names != {"pyyaml", "jsonschema"}:
            raise RuntimeError(f"unexpected base requirements: {base_requirements}")
        if any("jsonschema[" in value.lower() for value in base_requirements):
            raise RuntimeError("jsonschema extras are forbidden in runtime metadata")

        required_wheel_files = {
            "goverdocs/__init__.py",
            "goverdocs/cli.py",
        }
        missing_wheel_files = sorted(required_wheel_files - names)
        if missing_wheel_files:
            raise RuntimeError(
                f"wheel is missing package files: {missing_wheel_files}"
            )

        wheel_license_candidates = sorted(
            name
            for name in names
            if name.endswith("/licenses/LICENSE") or name == "LICENSE"
        )
        if not wheel_license_candidates:
            raise RuntimeError("wheel does not contain a PEP 639 LICENSE file")
        if not any(
            archive.read(name) == root_license
            for name in wheel_license_candidates
        ):
            raise RuntimeError("wheel LICENSE does not match repository LICENSE")

    source_commit, source_dirty = _source_state()
    manifest = {
        "schema_version": 1,
        "project": project_name,
        "version": version,
        "source_commit": source_commit,
        "source_dirty": source_dirty,
        "license_expression": license_expression,
        "license_sha256": _sha256_bytes(root_license),
        "artifacts": [
            {
                "filename": path.name,
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in sorted((sdist, wheel), key=lambda item: item.name)
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"SDIST={sdist.name}")
    print(f"SDIST_SHA256={_sha256_file(sdist)}")
    print(f"WHEEL={wheel.name}")
    print(f"WHEEL_SHA256={_sha256_file(wheel)}")
    print(f"ARTIFACT_MANIFEST={manifest_path}")
    print("ARTIFACT_CONTENT=VERIFIED")




def _safe_sdist_member_name(name: str) -> PurePosixPath:
    if not name or name.startswith("/") or "\\" in name:
        raise RuntimeError(f"unsafe sdist member path: {name!r}")

    path = PurePosixPath(name)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise RuntimeError(f"unsafe sdist member path: {name!r}")
    return path


def _sdist_payload(
    path: Path,
) -> dict[str, tuple[str, int, bytes]]:
    payload: dict[str, tuple[str, int, bytes]] = {}

    with tarfile.open(path, mode="r:gz") as archive:
        for member in archive.getmembers():
            normalized = _safe_sdist_member_name(member.name)
            name = normalized.as_posix()

            if name in payload:
                raise RuntimeError(f"duplicate sdist member: {name}")

            if member.isdir():
                payload[name] = ("directory", 0o755, b"")
                continue

            if not member.isfile():
                raise RuntimeError(
                    "unsupported sdist member type "
                    f"path={name} type={member.type!r}"
                )

            extracted = archive.extractfile(member)
            if extracted is None:
                raise RuntimeError(f"cannot read sdist member: {name}")

            mode = 0o755 if member.mode & 0o111 else 0o644
            payload[name] = ("file", mode, extracted.read())

    if not payload:
        raise RuntimeError(f"sdist contains no members: {path}")

    roots = {PurePosixPath(name).parts[0] for name in payload}
    if len(roots) != 1:
        raise RuntimeError(
            f"sdist must contain one top-level directory: {sorted(roots)}"
        )

    return payload


def compare_sdist_payload(left: Path, right: Path) -> None:
    left_payload = _sdist_payload(left)
    right_payload = _sdist_payload(right)

    if set(left_payload) != set(right_payload):
        raise RuntimeError(
            "sdist payload member sets differ: "
            f"left_only={sorted(set(left_payload) - set(right_payload))} "
            f"right_only={sorted(set(right_payload) - set(left_payload))}"
        )

    for name in sorted(left_payload):
        left_kind, left_mode, left_data = left_payload[name]
        right_kind, right_mode, right_data = right_payload[name]

        if (left_kind, left_mode) != (right_kind, right_mode):
            raise RuntimeError(
                "sdist payload metadata differs: "
                f"path={name} "
                f"left={(left_kind, oct(left_mode))} "
                f"right={(right_kind, oct(right_mode))}"
            )

        if left_data != right_data:
            raise RuntimeError(
                "sdist payload bytes differ: "
                f"path={name} "
                f"left={_sha256_bytes(left_data)} "
                f"right={_sha256_bytes(right_data)}"
            )

    print(f"SDIST_PAYLOAD_MEMBER_COUNT={len(left_payload)}")
    print("SDIST_PAYLOAD_CONTENT=IDENTICAL")
    print("SDIST_NONDETERMINISM_CLASSIFICATION=ARCHIVE_METADATA_ONLY")


def _canonical_sdist_bytes(path: Path, epoch: int) -> bytes:
    if epoch < 0:
        raise RuntimeError(f"SOURCE_DATE_EPOCH must be non-negative: {epoch}")

    payload = _sdist_payload(path)
    tar_buffer = io.BytesIO()

    with tarfile.open(
        fileobj=tar_buffer,
        mode="w",
        format=tarfile.PAX_FORMAT,
    ) as archive:
        for name in sorted(payload):
            kind, mode, data = payload[name]
            member = tarfile.TarInfo(name=name)
            member.uid = 0
            member.gid = 0
            member.uname = ""
            member.gname = ""
            member.mtime = epoch
            member.mode = mode
            member.pax_headers = {}

            if kind == "directory":
                member.type = tarfile.DIRTYPE
                member.size = 0
                archive.addfile(member)
            else:
                member.type = tarfile.REGTYPE
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))

    output = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        compresslevel=9,
        fileobj=output,
        mtime=epoch,
    ) as compressed:
        compressed.write(tar_buffer.getvalue())

    return output.getvalue()


def canonicalize_sdist(path: Path, epoch: int) -> None:
    original_payload = _sdist_payload(path)
    canonical = _canonical_sdist_bytes(path, epoch)

    temporary = path.with_name(f".{path.name}.canonical.tmp")
    temporary.write_bytes(canonical)
    os.chmod(temporary, 0o644)
    temporary.replace(path)

    if _sdist_payload(path) != original_payload:
        raise RuntimeError("canonicalization changed sdist payload content")

    if _canonical_sdist_bytes(path, epoch) != canonical:
        raise RuntimeError("sdist canonicalization is not idempotent")

    with path.open("rb") as handle:
        header = handle.read(10)
    gzip_mtime = int.from_bytes(header[4:8], "little")
    if gzip_mtime != epoch:
        raise RuntimeError(
            f"canonical gzip mtime mismatch: expected={epoch} actual={gzip_mtime}"
        )

    with tarfile.open(path, mode="r:gz") as archive:
        for member in archive.getmembers():
            if member.mtime != epoch:
                raise RuntimeError(
                    "canonical tar member mtime mismatch: "
                    f"path={member.name} expected={epoch} actual={member.mtime}"
                )
            if member.uid != 0 or member.gid != 0:
                raise RuntimeError(
                    "canonical tar ownership mismatch: "
                    f"path={member.name} uid={member.uid} gid={member.gid}"
                )
            if member.uname or member.gname:
                raise RuntimeError(
                    "canonical tar owner names are not empty: "
                    f"path={member.name}"
                )

    print(f"CANONICAL_SDIST={path.name}")
    print(f"CANONICAL_SDIST_SHA256={_sha256_file(path)}")
    print(f"CANONICAL_SDIST_EPOCH={epoch}")
    print("CANONICAL_SDIST_PAYLOAD_PRESERVED=VERIFIED")
    print("CANONICAL_SDIST_IDEMPOTENCE=VERIFIED")

def verify_reproducible(left: Path, right: Path) -> None:
    left_files = {path.name: path for path in left.iterdir() if path.is_file()}
    right_files = {path.name: path for path in right.iterdir() if path.is_file()}

    if set(left_files) != set(right_files):
        raise RuntimeError(
            "reproducibility directories contain different filenames: "
            f"left={sorted(left_files)} right={sorted(right_files)}"
        )

    if not left_files:
        raise RuntimeError("reproducibility directories contain no artifacts")

    for filename in sorted(left_files):
        left_hash = _sha256_file(left_files[filename])
        right_hash = _sha256_file(right_files[filename])
        if left_hash != right_hash:
            raise RuntimeError(
                f"artifact is not reproducible: {filename} "
                f"left={left_hash} right={right_hash}"
            )
        print(f"REPRODUCIBLE_ARTIFACT filename={filename} sha256={left_hash}")

    print("REPRODUCIBLE_BUILD=VERIFIED")


def _installed_distributions() -> dict[str, metadata.Distribution]:
    return {
        _canonical_name(distribution.metadata["Name"]): distribution
        for distribution in metadata.distributions()
        if distribution.metadata.get("Name")
    }


def _runtime_closure(
    installed: dict[str, metadata.Distribution],
    root_name: str,
) -> list[metadata.Distribution]:
    pending: deque[str] = deque([_canonical_name(root_name)])
    visited: set[str] = set()
    result: list[metadata.Distribution] = []

    while pending:
        name = pending.popleft()
        if name in visited:
            continue
        visited.add(name)

        distribution = installed.get(name)
        if distribution is None:
            raise RuntimeError(f"required distribution is not installed: {name}")
        result.append(distribution)

        for requirement in distribution.requires or []:
            if _is_optional_requirement(requirement):
                continue
            dependency = _requirement_name(requirement)
            if dependency in installed and dependency not in visited:
                pending.append(dependency)

    return sorted(
        result,
        key=lambda item: _canonical_name(str(item.metadata["Name"])),
    )


def _declared_license(distribution: metadata.Distribution) -> str:
    expression = distribution.metadata.get("License-Expression")
    if expression:
        return str(expression).strip()

    legacy = distribution.metadata.get("License")
    if legacy and str(legacy).strip() not in {"", "UNKNOWN"}:
        return str(legacy).strip()

    classifiers = distribution.metadata.get_all("Classifier", [])
    license_classifiers = [
        value.removeprefix("License :: ").strip()
        for value in classifiers
        if value.startswith("License :: ")
    ]
    return " | ".join(license_classifiers) if license_classifiers else "UNKNOWN"


def _license_is_forbidden(value: str) -> bool:
    upper_value = value.upper()
    return any(
        marker in upper_value
        for marker in FORBIDDEN_LICENSE_MARKERS
    )


def verify_environment(output_path: Path) -> None:
    project = _project_metadata()
    installed = _installed_distributions()
    closure = _runtime_closure(installed, str(project["name"]))

    inventory: list[dict[str, str]] = []
    for distribution in closure:
        name = str(distribution.metadata["Name"])
        canonical_name = _canonical_name(name)
        declared_license = _declared_license(distribution)

        if canonical_name in FORBIDDEN_RUNTIME_DISTRIBUTIONS:
            raise RuntimeError(f"forbidden runtime distribution installed: {name}")
        if declared_license == "UNKNOWN":
            raise RuntimeError(f"runtime distribution has unknown license: {name}")

        if _license_is_forbidden(declared_license):
            raise RuntimeError(
                f"runtime distribution has forbidden license marker: "
                f"{name} ({declared_license})"
            )

        inventory.append(
            {
                "name": name,
                "version": distribution.version,
                "license": declared_license,
            }
        )

    output = {
        "schema_version": 1,
        "root_project": str(project["name"]),
        "runtime_distributions": inventory,
    }
    output_path.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"RUNTIME_DISTRIBUTION_COUNT={len(inventory)}")
    for item in inventory:
        print(
            "RUNTIME_DISTRIBUTION "
            f"name={item['name']} "
            f"version={item['version']} "
            f"license={item['license']}"
        )
    print(f"RUNTIME_DEPENDENCY_INVENTORY={output_path}")
    print("RUNTIME_DEPENDENCY_AUDIT=PASS")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify GOVERDOCS release distributions and runtime closure"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    artifacts = subparsers.add_parser("artifacts")
    artifacts.add_argument("--dist-dir", type=Path, required=True)
    artifacts.add_argument("--manifest", type=Path, required=True)

    compare_payload = subparsers.add_parser("compare-sdist-payload")
    compare_payload.add_argument("--left", type=Path, required=True)
    compare_payload.add_argument("--right", type=Path, required=True)

    canonicalize = subparsers.add_parser("canonicalize-sdist")
    canonicalize.add_argument("--path", type=Path, required=True)
    canonicalize.add_argument("--epoch", type=int, required=True)

    compare = subparsers.add_parser("compare")
    compare.add_argument("--left", type=Path, required=True)
    compare.add_argument("--right", type=Path, required=True)

    environment = subparsers.add_parser("environment")
    environment.add_argument("--output", type=Path, required=True)

    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "artifacts":
        args.dist_dir.mkdir(parents=True, exist_ok=True)
        verify_artifacts(args.dist_dir, args.manifest)
        return 0
    if args.command == "compare-sdist-payload":
        compare_sdist_payload(args.left, args.right)
        return 0
    if args.command == "canonicalize-sdist":
        canonicalize_sdist(args.path, args.epoch)
        return 0
    if args.command == "compare":
        verify_reproducible(args.left, args.right)
        return 0
    if args.command == "environment":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        verify_environment(args.output)
        return 0
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
