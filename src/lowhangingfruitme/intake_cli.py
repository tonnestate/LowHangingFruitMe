"""Read-only local import CLI, not a public HTTP upload or invoice service."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from .documents import extract_pdf
from .intake import audit_from_csv
from .approval import key_from_environment
from .approval_registry import ApprovalRegistry
from .universal_import import inspect_source, normalize_source, audit_from_sources

def main() -> int:
    parser = argparse.ArgumentParser(description="LowHangingFruitMe source intake")
    sub = parser.add_subparsers(dest="action", required=True)
    csv_cmd = sub.add_parser("audit-csv", help="Validate canonical CSV and audit")
    csv_cmd.add_argument("--rule", required=True, type=Path)
    csv_cmd.add_argument("--transactions", required=True, type=Path)
    csv_cmd.add_argument("--settlements", required=True, type=Path)
    csv_cmd.add_argument("--source-system", required=True)
    csv_cmd.add_argument("--approval", type=Path, help="Signed approval receipt JSON")
    csv_cmd.add_argument("--contract-source", type=Path, help="Exact reviewed contract source file")
    csv_cmd.add_argument("--tenant-id", help="Tenant identity from trusted scope")
    csv_cmd.add_argument("--legal-entity-id", help="Legal entity identity from trusted scope")
    csv_cmd.add_argument("--controls", type=Path, help="Separate ERP source-control report JSON")
    csv_cmd.add_argument("--confirm-transactions-complete", action="store_true")
    csv_cmd.add_argument("--confirm-settlements-complete", action="store_true")
    csv_cmd.add_argument("--confirm-agreements-complete", action="store_true")
    pdf_cmd = sub.add_parser("extract-pdf", help="Extract cited PDF segments with Docling")
    pdf_cmd.add_argument("--file", required=True, type=Path)
    inspect_cmd = sub.add_parser("inspect-source", help="Inspect CSV, XLSX, invoice XML or document")
    inspect_cmd.add_argument("--file", required=True, type=Path)
    inspect_cmd.add_argument("--dataset", choices=("transactions", "settlements"))
    inspect_cmd.add_argument("--sheet")
    norm_cmd = sub.add_parser("normalize-source", help="Write reviewed canonical CSV without replacing source")
    norm_cmd.add_argument("--file", required=True, type=Path)
    norm_cmd.add_argument("--dataset", required=True, choices=("transactions", "settlements"))
    norm_cmd.add_argument("--source-system", required=True)
    norm_cmd.add_argument("--plan", required=True, type=Path)
    norm_cmd.add_argument("--output", required=True, type=Path)
    source_cmd = sub.add_parser(
        "audit-sources", help="One verified import-mapping-audit run for reviewed CSV/XLSX")
    source_cmd.add_argument("--rule", required=True, type=Path)
    source_cmd.add_argument("--transactions", required=True, type=Path)
    source_cmd.add_argument("--settlements", required=True, type=Path)
    source_cmd.add_argument("--transaction-plan", required=True, type=Path)
    source_cmd.add_argument("--settlement-plan", required=True, type=Path)
    source_cmd.add_argument("--approval", required=True, type=Path)
    source_cmd.add_argument("--contract-source", required=True, type=Path)
    source_cmd.add_argument("--controls", required=True, type=Path)
    source_cmd.add_argument("--source-system", required=True)
    source_cmd.add_argument("--tenant-id", required=True)
    source_cmd.add_argument("--legal-entity-id", required=True)
    source_cmd.add_argument("--confirm-transactions-complete", action="store_true")
    source_cmd.add_argument("--confirm-settlements-complete", action="store_true")
    source_cmd.add_argument("--confirm-agreements-complete", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "audit-csv":
            output = audit_from_csv(
                args.rule, args.transactions, args.settlements,
                source_system=args.source_system,
                approval_receipt=json.loads(args.approval.read_text(encoding="utf-8")) if args.approval else None,
                approval_key=key_from_environment() if args.approval else None,
                approval_scope={"tenant_id": args.tenant_id, "legal_entity_id": args.legal_entity_id}
                    if args.approval else None,
                contract_source_path=args.contract_source,
                approval_registry=ApprovalRegistry.from_environment() if args.approval else None,
                controls=json.loads(args.controls.read_text(encoding="utf-8")) if args.controls else None,
                completeness={
                    "transactions_complete": args.confirm_transactions_complete,
                    "settlements_complete": args.confirm_settlements_complete,
                    "agreements_complete": args.confirm_agreements_complete,
                },
            )
        elif args.action == "audit-sources":
            output = audit_from_sources(
                rule_path=args.rule, transactions_source=args.transactions,
                settlements_source=args.settlements,
                transaction_plan=json.loads(args.transaction_plan.read_text(encoding="utf-8")),
                settlement_plan=json.loads(args.settlement_plan.read_text(encoding="utf-8")),
                source_system=args.source_system,
                controls=json.loads(args.controls.read_text(encoding="utf-8")),
                completeness={
                    "transactions_complete": args.confirm_transactions_complete,
                    "settlements_complete": args.confirm_settlements_complete,
                    "agreements_complete": args.confirm_agreements_complete,
                },
                approval_receipt=json.loads(args.approval.read_text(encoding="utf-8")),
                approval_key=key_from_environment(),
                approval_scope={"tenant_id":args.tenant_id,
                                "legal_entity_id":args.legal_entity_id},
                contract_source_path=args.contract_source,
                approval_registry=ApprovalRegistry.from_environment(),
            )
        elif args.action == "extract-pdf":
            output = extract_pdf(args.file)
        elif args.action == "inspect-source":
            output = inspect_source(args.file, dataset=args.dataset, sheet_name=args.sheet)
        else:
            mapping_plan = json.loads(args.plan.read_text(encoding="utf-8"))
            report = normalize_source(args.file, dataset=args.dataset,
                                      source_system=args.source_system, plan=mapping_plan)
            canonical = report.pop("canonical_csv")
            if not args.output.parent.is_dir() or args.output.is_symlink():
                raise ValueError("output directory missing or output is a symlink")
            with args.output.open("x", encoding="utf-8", newline="") as target:
                target.write(canonical)
            output = {**report, "canonical_file_written": str(args.output)}
    except (ValueError, KeyError, TypeError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"intake rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.action in ("audit-csv", "audit-sources") and output["status"] != "EVIDENCED" else 0

if __name__ == "__main__":
    raise SystemExit(main())
