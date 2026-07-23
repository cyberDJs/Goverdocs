from pathlib import Path
from types import SimpleNamespace

from goverdocs import cli


def test_rebuild_index_updates_status_summary(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    index_path = tmp_path / "DOCUMENTATION_INDEX.md"
    registry = {
        "generated_at": "2026-07-23T15:00:00+00:00",
        "documents": [],
    }
    calls: list[str] = []

    config = SimpleNamespace(
        root=tmp_path,
        policy_path=tmp_path / "policy.yaml",
    )

    monkeypatch.setattr(
        cli,
        "load_config",
        lambda root: config,
    )
    monkeypatch.setattr(
        cli,
        "rebuild_index",
        lambda root, policy_path: index_path,
    )
    monkeypatch.setattr(
        cli,
        "write_registry",
        lambda root, policy_path: registry,
    )

    def record_relationship_graph(
        root: Path,
        current_registry: dict,
    ) -> None:
        assert root == tmp_path
        assert current_registry is registry
        calls.append("relationship-graph")

    def record_status_summary(
        root: Path,
        current_registry: dict,
    ) -> dict:
        assert root == tmp_path
        assert current_registry is registry
        calls.append("status-summary")
        return {
            "generated_at": registry["generated_at"],
            "document_count": 0,
            "status_counts": {},
        }

    monkeypatch.setattr(
        cli,
        "write_relationship_graph",
        record_relationship_graph,
    )
    monkeypatch.setattr(
        cli,
        "write_status_summary",
        record_status_summary,
    )

    result = cli.main(
        [
            "rebuild-index",
            "--root",
            str(tmp_path),
        ]
    )

    output = capsys.readouterr().out

    assert result == 0
    assert calls == [
        "relationship-graph",
        "status-summary",
    ]
    assert "UPDATED manifests/DOCUMENT_STATUS_SUMMARY.json" in output
