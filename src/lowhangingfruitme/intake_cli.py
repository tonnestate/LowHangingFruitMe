"""Read-only local import CLI, not a public HTTP upload or invoice service."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from .documents import extract_pdf
from .intake import audit_from_csv

def main() -> int:
    parser = argparse.ArgumentParser(description="LowHangingFruitMe source intake")
    sub = parser.add_subparsers(dest="action", required=True)
    csv_cmd = sub.add_parser("audit-csv", help="Validate canonical CSV and audit")
    csv_cmd.add_argument("--rule", required=True, type=Path)
    csv_cmd.add_argument("--transactions", required=True, type=Path)
    csv_cmd.add_argument("--settlements", required=True, type=Path)
    csv_cmd.add_argument("--source-system", required=True)
    csv_cmd.add_argument("--confirm-transactions-complete", action="store_true")
    csv_cmd.add_argument("--confirm-settlements-complete", action="store_true")
    csv_cmd.add_argument("--confirm-agreements-complete", action="store_true")
    pdf_cmd = sub.add_parser("extract-pdf", help="Extract cited PDF segments with Docling")
    pdf_cmd.add_argument("--file", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.action == "audit-csv":
            output = audit_from_csv(
                args.rule, args.transactions, args.settlements,
                source_system=args.source_system,
                completeness={
                    "transactions_complete": args.confirm_transactions_complete,
                    "settlements_complete": args.confirm_settlements_complete,
                    "agreements_complete": args.confirm_agreements_complete,
                },
            )
        else:
            output = extract_pdf(args.file)
    except (ValueError, KeyError, TypeError, OSError, RuntimeError) as exc:
        print(f"intake rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.action == "audit-csv" and output["status"] != "EVIDENCED" else 0

if __name__ == "__main__":
    raise SystemExit(main())
