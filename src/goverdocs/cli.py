from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .classifier import changed_from_git, classify
from .config import load_config
from .gate import evaluate_gate
from .indexer import rebuild_index
from .initializer import initialize_project
from .planner import plan
from .receipts import create_receipt
from .registry import (
    build_registry,
    write_registry,
    write_relationship_graph,
    write_status_summary,
)
from .validator import validate_project


def _root(value: str | None) -> Path:
    return Path(value).expanduser().resolve() if value else Path.cwd().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="goverdocs", description="Deterministic documentation governor")
    parser.add_argument("--version", action="version", version="goverdocs 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("target", nargs="?", default=".")
    init.add_argument("--project-name")
    init.add_argument("--force", action="store_true")
    inspect = sub.add_parser("inspect")
    inspect.add_argument("--root")
    inspect.add_argument("--json", action="store_true")
    for name in ("classify", "plan"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--root")
        cmd.add_argument("--diff", default="HEAD~1..HEAD")
        cmd.add_argument("--changed-file", action="append", default=[])
        cmd.add_argument("--diff-text-file")
        cmd.add_argument("--json", action="store_true")
    gate = sub.add_parser("gate")
    gate.add_argument("--root")
    gate.add_argument("--diff", default="HEAD~1..HEAD")
    gate.add_argument("--changed-file", action="append", default=[])
    gate.add_argument("--diff-text-file")
    gate.add_argument("--as-of", help="Evaluation date in YYYY-MM-DD; defaults to today")
    gate.add_argument("--json", action="store_true")
    gate.add_argument("--receipt", action="store_true")
    validate = sub.add_parser("validate")
    validate.add_argument("--root")
    validate.add_argument("--json", action="store_true")
    validate.add_argument("--receipt", action="store_true")
    index = sub.add_parser("rebuild-index")
    index.add_argument("--root")
    health = sub.add_parser("health")
    health.add_argument("--root")
    health.add_argument("--receipt", action="store_true")
    return parser


def _change_input(root: Path, diff_spec: str, changed_files: list[str], diff_text_file: str | None) -> tuple[list[str], str]:
    if changed_files:
        text = Path(diff_text_file).read_text(encoding="utf-8") if diff_text_file else ""
        return changed_files, text
    return changed_from_git(root, diff_spec)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            target = _root(args.target)
            written = initialize_project(target, args.project_name or target.name, args.force)
            print(f"INITIALIZED {target}")
            for path in written:
                print(f"CREATE {path.relative_to(target)}")
            return 0
        root = _root(getattr(args, "root", None))
        config = load_config(root)
        if args.command == "inspect":
            registry = build_registry(config.root, config.policy_path)
            if args.json:
                print(json.dumps(registry, ensure_ascii=False, indent=2))
            else:
                print(f"PROJECT={config.project_name}\nROOT={config.root}\nDOCUMENTS={len(registry['documents'])}")
                for item in registry["documents"]:
                    print(f"{str(item.get('id')):<24} {str(item.get('status')):<12} {item.get('path')}")
            return 0
        if args.command == "gate":
            files, diff_text = _change_input(config.root, args.diff, args.changed_file, args.diff_text_file)
            evaluation_date = date.fromisoformat(args.as_of) if args.as_of else date.today()
            report = evaluate_gate(
                root=config.root,
                policy_path=config.policy_path,
                matrix_path=config.matrix_path,
                metadata_schema_path=config.metadata_schema_path,
                change_gate_path=config.change_gate_path,
                change_gate_schema_path=config.change_gate_schema_path,
                changed_files=files,
                diff_text=diff_text,
                as_of=evaluation_date,
            )
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(f"GOVERNANCE GATE={report['status']}")
                print(f"EVALUATION_DATE={report['evaluation_date']}")
                print(f"INPUT_DIGEST={report['input']['digest']}")
                print(f"EVENTS={len(report['events'])}")
                print(f"OBLIGATIONS={len(report['obligations'])}")
                print(f"EVIDENCE_GAPS={len(report['evidence_gaps'])}")
                for gap in report["evidence_gaps"]:
                    marker = "BLOCK" if gap["blocking"] else "WARN"
                    print(f"{marker:<5} {gap['code']:<24} {gap['subject']}: {gap['message']}")
            if args.receipt:
                receipt = create_receipt(config.root, "gate", report["status"].lower(), gate_report=report)
                print(f"RECEIPT={receipt}")
            return 1 if report["status"] == "BLOCKED" else 0
        if args.command in {"classify", "plan"}:
            files, diff_text = _change_input(config.root, args.diff, args.changed_file, args.diff_text_file)
            events = classify(files, diff_text)
            if args.command == "classify":
                if args.json:
                    print(json.dumps([event.to_dict() for event in events], ensure_ascii=False, indent=2))
                else:
                    print("DOCUMENTATION EVENTS")
                    for event in events:
                        print(f"{event.name:<40} confidence={event.confidence:.2f}")
                        for reason in event.reasons:
                            print(f"  - {reason}")
                return 0
            operations = plan(events, config.matrix_path)
            if args.json:
                print(json.dumps({"events": [event.to_dict() for event in events], "operations": [op.to_dict() for op in operations]}, ensure_ascii=False, indent=2))
            else:
                print("DOCUMENTATION EVENTS")
                for event in events:
                    print(f"- {event.name} ({event.confidence:.2f})")
                print("\nPLANNED ACTIONS")
                for operation in operations:
                    marker = "APPROVAL" if operation.approval_required else "AUTO"
                    print(f"{operation.action.upper():<16} {operation.target} [{operation.rule_id} | {marker}]")
                print("\nRESULT")
                print("Canonical write: BLOCKED — approval required" if any(op.approval_required for op in operations) else "Canonical write: eligible after validation")
            return 0
        if args.command == "validate":
            issues = validate_project(
                config.root,
                config.policy_path,
                config.metadata_schema_path,
                config.change_gate_path,
                config.change_gate_schema_path,
            )
            if args.json:
                print(json.dumps([issue.to_dict() for issue in issues], ensure_ascii=False, indent=2))
            else:
                print(f"VALIDATION ROOT={config.root}")
                print("PASS — no issues" if not issues else f"FAIL — {len(issues)} issue(s)")
                for issue in issues:
                    print(f"{issue.severity.upper():<7} {issue.code:<24} {issue.path}: {issue.message}")
            if args.receipt:
                receipt = create_receipt(config.root, "validate", "failed" if issues else "passed", issues=[issue.to_dict() for issue in issues])
                print(f"RECEIPT={receipt}")
            return 1 if issues else 0
        if args.command == "rebuild-index":
            target = rebuild_index(config.root, config.policy_path)
            registry = write_registry(config.root, config.policy_path)
            write_relationship_graph(config.root, registry)
            write_status_summary(config.root, registry)
            print(f"UPDATED {target.relative_to(config.root)}")
            print("UPDATED manifests/DOCUMENT_REGISTRY.yaml")
            print("UPDATED manifests/RELATIONSHIP_GRAPH.json")
            print("UPDATED manifests/DOCUMENT_STATUS_SUMMARY.json")
            return 0
        if args.command == "health":
            registry = build_registry(config.root, config.policy_path)
            issues = validate_project(
                config.root,
                config.policy_path,
                config.metadata_schema_path,
                config.change_gate_path,
                config.change_gate_schema_path,
            )
            print(f"PROJECT={config.project_name}\nDOCUMENTS={len(registry['documents'])}\nISSUES={len(issues)}\nSTATUS={'PASS' if not issues else 'FAIL'}")
            if args.receipt:
                receipt = create_receipt(config.root, "health", "passed" if not issues else "failed", document_count=len(registry["documents"]), issues=[issue.to_dict() for issue in issues])
                print(f"RECEIPT={receipt}")
            return 1 if issues else 0
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
