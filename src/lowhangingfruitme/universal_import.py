"""Universal local source intake: inspect -> reviewed mapping -> canonical CSV.

Supports arbitrary-column UTF-8 CSV and bounded XLSX worksheets. XML invoices,
PDF contracts and DOCX agreements are classified as documents for separate
adapters, never silently interpreted as posted ledger entries.

Untrusted files require isolated scanning before invoking these local helpers.
"""
from __future__ import annotations

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import tempfile
from typing import Any
from zipfile import ZipFile, BadZipFile

from .intake import COLUMNS, audit_from_csv
from .rebate import Entry

MAX_SOURCE_BYTES = 16 * 1024 * 1024
MAX_ROWS = 100_000
MAX_ARCHIVE_UNCOMPRESSED = 40 * 1024 * 1024
MAX_CELLS = 1_500_000
FORMATS = {".csv": "CSV_TABLE", ".xlsx": "XLSX_TABLE",
           ".xml": "XML_DOCUMENT", ".pdf": "PDF_DOCUMENT",
           ".docx": "DOCX_DOCUMENT"}
ALIASES = {
    "external_id": ("belegnummer", "beleg_nr", "rechnungsnummer", "invoice_number", "document_id", "gutschriftnummer", "id"),
    "supplier_id": ("kreditor", "kreditorennummer", "lieferant", "lieferanten_nr", "supplier", "vendor_id"),
    "date": ("belegdatum", "buchungsdatum", "rechnungsdatum", "invoice_date", "posting_date"),
    "currency": ("waehrung", "währung", "currency", "ccy"),
    "amount_net": ("nettobetrag", "netto", "betrag_netto", "net_amount", "net_total", "net_value"),
    "kind": ("belegart", "vorgangstyp", "transaction_type", "type"),
    "posted": ("gebucht", "buchungsstatus", "posting_status", "is_posted"),
    "basis": ("berechnungsbasis", "basis", "bonus_basis"),
    "agreement_id": ("vertragsnr", "vertragsnummer", "agreement", "agreement_reference"),
    "period_start": ("bonus_von", "periode_von", "period_start"),
    "period_end": ("bonus_bis", "periode_bis", "period_end"),
}


def _source(path: str | Path) -> tuple[Path, str, str]:
    path = Path(path)
    if path.suffix.lower() not in FORMATS or path.is_symlink() or not path.is_file():
        raise ValueError("unsupported source format, symlink or nonregular file")
    if not 0 < path.stat().st_size <= MAX_SOURCE_BYTES:
        raise ValueError("source file empty or beyond 16 MB limit")
    data = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix == ".pdf" and not data.startswith(b"%PDF-"):
        raise ValueError("invalid PDF magic")
    if suffix in (".xlsx", ".docx"):
        if not data.startswith(b"PK"):
            raise ValueError("invalid Office ZIP magic")
        try:
            with ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > 5000 or sum(z.file_size for z in entries) > MAX_ARCHIVE_UNCOMPRESSED:
                    raise ValueError("Office ZIP exceeds extraction budget")
                if any(z.file_size > 0 and z.file_size > max(z.compress_size, 1) * 200
                       for z in entries):
                    raise ValueError("Office ZIP suspicious compression ratio")
                names = {z.filename for z in entries}
                core = "xl/workbook.xml" if suffix == ".xlsx" else "word/document.xml"
                if core not in names:
                    raise ValueError("unrecognized Office document layout")
        except BadZipFile as exc:
            raise ValueError("invalid Office ZIP") from exc
    if suffix == ".xml":
        if b"\0" in data:
            raise ValueError("invalid XML null byte")
        try:
            from defusedxml import ElementTree as ET
        except ImportError as exc:
            raise RuntimeError("install lowhangingfruitme[universal] for XML classification") from exc
        try:
            element = ET.fromstring(data)
        except ET.ParseError as exc:
            raise ValueError("malformed or unsafe XML document") from exc
        root = element.tag.split("}")[-1]
        if root not in ("Invoice", "CreditNote", "CrossIndustryInvoice"):
            raise ValueError("XML is not a recognized invoice document; review required")
    if suffix == ".csv":
        if b"\0" in data:
            raise ValueError("invalid CSV null byte")
        try:
            data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("CSV must be UTF-8") from exc
    return path, sha256(data).hexdigest(), FORMATS[suffix]


def _headers(rows: list[Any]) -> list[str]:
    if not rows or not rows[0]:
        raise ValueError("tabular file has no header")
    header = [str(value).strip() if value is not None else "" for value in rows[0]]
    if any(not v for v in header):
        raise ValueError("empty header columns are not accepted")
    if len(set(v.casefold() for v in header)) != len(header):
        raise ValueError("duplicate case-insensitive headers")
    return header


def _table(path: Path, kind: str, *, sheet_name: str | None = None) -> tuple[list[str], list[tuple[int, dict[str, Any]]], dict[str, Any]]:
    if kind == "CSV_TABLE":
        if sheet_name is not None:
            raise ValueError("sheet_name is supported only for XLSX")
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            first = stream.readline()
            delimiter = max((",", ";", "\t"), key=first.count)
            if first.count(delimiter) < 1:
                raise ValueError("CSV delimiter could not be determined")
            stream.seek(0)
            reader = csv.reader(stream, delimiter=delimiter, strict=True)
            header = _headers([next(reader, [])])
            parsed: list[tuple[int, dict[str, Any]]] = []
            for number, values in enumerate(reader, start=2):
                if number - 1 > MAX_ROWS:
                    raise ValueError("source exceeds row limit")
                if len(values) != len(header):
                    raise ValueError(f"line {number}: column count does not match header")
                if not any(str(v).strip() for v in values):
                    continue
                parsed.append((number, dict(zip(header, values))))
        return header, parsed, {"delimiter": delimiter}
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("install lowhangingfruitme[universal] for XLSX intake") from exc
    workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
    try:
        if sheet_name is None:
            if len(workbook.sheetnames) != 1:
                raise ValueError("XLSX has multiple sheets; select one explicitly")
            sheet_name = workbook.sheetnames[0]
        if sheet_name not in workbook.sheetnames:
            raise ValueError("requested XLSX sheet not found")
        sheet = workbook[sheet_name]
        if sheet.max_row and sheet.max_column and sheet.max_row * sheet.max_column > MAX_CELLS:
            raise ValueError("XLSX exceeds cell budget")
        iterator = sheet.iter_rows(values_only=True)
        header = _headers([next(iterator, ())])
        parsed = []
        for number, values in enumerate(iterator, start=2):
            if number - 1 > MAX_ROWS:
                raise ValueError("XLSX exceeds row limit")
            if len(values) > len(header) and any(v is not None for v in values[len(header):]):
                raise ValueError(f"row {number}: unexpected extra columns")
            if not any(v is not None and str(v).strip() for v in values):
                continue
            if any(isinstance(v, str) and v.startswith("=") for v in values):
                raise ValueError(f"row {number}: formulas require manual verified values")
            parsed.append((number, dict(zip(header, values))))
        return header, parsed, {"sheet": sheet_name}
    finally:
        workbook.close()


def _suggest(header: list[str], dataset: str) -> dict[str, list[str]]:
    suggestions = {}
    for field in COLUMNS[dataset]:
        patterns = {field.casefold(), *(v.casefold() for v in ALIASES.get(field, ()))}
        hits = [h for h in header if h.casefold() in patterns]
        suggestions[field] = hits
    return suggestions


def inspect_source(path: str | Path, *, dataset: str | None = None,
                   sheet_name: str | None = None) -> dict[str, Any]:
    """No implicit approval, unknown formats or speculative mappings."""
    src, digest, kind = _source(path)
    result: dict[str, Any] = {
        "format": kind, "source_sha256": digest,
        "state": "REQUIRES_REVIEW",
        "normalized": False, "audit_ready": False,
    }
    if kind not in ("CSV_TABLE", "XLSX_TABLE"):
        result["route"] = ("document_pdf" if kind == "PDF_DOCUMENT"
                           else "document_office" if kind == "DOCX_DOCUMENT"
                           else "einvoice_xml_review")
        return result
    header, rows, options = _table(src, kind, sheet_name=sheet_name)
    result.update(headers=header, rows=len(rows), options=options)
    if dataset is not None:
        if dataset not in COLUMNS:
            raise ValueError("unknown canonical dataset")
        result["proposed_mapping"] = _suggest(header, dataset)
        result["unmatched_columns"] = [
            h for h in header if not any(h in vals for vals in result["proposed_mapping"].values())
        ]
    return result


def _date_value(value: Any, fmt: str) -> str:
    if isinstance(value, (datetime, date)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    if not isinstance(value, str):
        raise ValueError("date source is not a string/date")
    value = value.strip()
    if fmt == "ISO":
        return date.fromisoformat(value).isoformat()
    if fmt == "DE":
        return datetime.strptime(value, "%d.%m.%Y").date().isoformat()
    raise ValueError("date_format must be ISO or DE")


def _amount(value: Any, fmt: str) -> str:
    if isinstance(value, bool) or value is None:
        raise ValueError("amount is not a number")
    raw = str(value).strip()
    if fmt == "DE":
        if not re.fullmatch(r"-?(?:[0-9]{1,3}(?:\.[0-9]{3})*|[0-9]+),[0-9]{1,2}", raw):
            raise ValueError("invalid German decimal formatting")
        raw = raw.replace(".", "").replace(",", ".")
    elif fmt == "DOT":
        if not re.fullmatch(r"-?[0-9]+(?:\.[0-9]{1,2})?", raw):
            raise ValueError("invalid dot decimal formatting")
    else:
        raise ValueError("decimal_format must be DOT or DE")
    try:
        amount = Decimal(raw)
        if not amount.is_finite():
            raise ValueError("non-finite amount")
        return format(amount.quantize(Decimal("0.01")), ".2f")
    except InvalidOperation as exc:
        raise ValueError("invalid monetary amount") from exc


def _bool(value: Any, fmt: str) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if not isinstance(value, str):
        raise ValueError("posted must be explicit boolean source")
    value = value.strip().casefold()
    allowed = {"true": "true", "false": "false"} if fmt == "EN" else {
        "ja": "true", "nein": "false"
    } if fmt == "DE" else {}
    if value not in allowed:
        raise ValueError("unrecognized posted boolean")
    return allowed[value]


def normalize_source(path: str | Path, *, dataset: str,
                     source_system: str, plan: dict[str, Any]) -> dict[str, Any]:
    """Normalize only a fully reviewed source-hash-bound mapping specification.

    Mapping 'confirmed' is an operator assertion, NOT authenticated approval
    and never substitutes for the HMAC/DB financial-audit controls.
    """
    src, digest, kind = _source(path)
    if kind not in ("CSV_TABLE", "XLSX_TABLE") or dataset not in COLUMNS:
        raise ValueError("only CSV/XLSX tables can become ERP ledger rows")
    if not isinstance(source_system, str) or not source_system.strip():
        raise ValueError("source_system is required")
    if not isinstance(plan, dict) or set(plan) != {
        "source_sha256", "dataset", "mapping", "constants",
        "sheet_name", "decimal_format", "date_format",
        "boolean_format", "reviewed_by", "confirmed"
    }:
        raise ValueError("explicit complete mapping plan required")
    if plan["confirmed"] is not True or not isinstance(plan["reviewed_by"], str) or not plan["reviewed_by"].strip():
        raise ValueError("source mapping requires explicit reviewer confirmation")
    if plan["dataset"] != dataset or plan["source_sha256"] != digest:
        raise ValueError("mapping plan is not bound to this exact source and dataset")
    header, rows, opts = _table(src, kind, sheet_name=plan["sheet_name"])
    mapping, constants = plan["mapping"], plan["constants"]
    if not isinstance(mapping, dict) or not isinstance(constants, dict):
        raise ValueError("mapping and constants must be objects")
    required = set(COLUMNS[dataset])
    if (set(mapping) | set(constants)) != required or (set(mapping) & set(constants)):
        raise ValueError("map every canonical field exactly once without overlap")
    if len(set(mapping.values())) != len(mapping) or any(v not in header for v in mapping.values()):
        raise ValueError("mapping refers to absent/duplicate source columns")
    if not {"external_id", "supplier_id", "date", "amount_net", "posted"}.issubset(mapping):
        raise ValueError("identity, date, amount and posted status must come from source columns")
    if dataset == "settlements" and not {"agreement_id", "period_start", "period_end"}.issubset(mapping):
        raise ValueError("settlement agreement and period must be backed by source columns")
    if any(key not in {"currency", "kind", "basis"} for key in constants):
        raise ValueError("constants allowed only for explicitly confirmed currency/kind/basis")
    if kind == "CSV_TABLE" and plan["sheet_name"] is not None:
        raise ValueError("CSV mapping must not specify a worksheet")
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=COLUMNS[dataset], lineterminator="\n")
    writer.writeheader()
    lineage = []
    identities: set[tuple[str, str]] = set()
    plan_hash = sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False,
                                  separators=(",", ":")).encode()).hexdigest()
    for row_num, row in rows:
        values: dict[str, Any] = {field: row[source] for field, source in mapping.items()}
        values.update(constants)
        try:
            canonical = {}
            for field in COLUMNS[dataset]:
                value = values[field]
                if field == "date" or field in ("period_start", "period_end") and value not in ("", None):
                    canonical[field] = _date_value(value, plan["date_format"])
                elif field == "amount_net":
                    canonical[field] = _amount(value, plan["decimal_format"])
                elif field == "posted":
                    canonical[field] = _bool(value, plan["boolean_format"])
                else:
                    canonical[field] = str(value).strip() if value is not None else ""
            entry = {**canonical, "source_system": source_system,
                     "evidence_refs": [f"sha256:{digest}#row={row_num}"]}
            entry["posted"] = canonical["posted"] == "true"
            if dataset == "settlements":
                entry["agreement_id"] = canonical["agreement_id"] or None
                entry["period_start"] = canonical["period_start"] or None
                entry["period_end"] = canonical["period_end"] or None
            Entry.load(entry, settlement=(dataset == "settlements"))
            identity = (source_system, canonical["external_id"])
            if identity in identities:
                raise ValueError("duplicate source ID")
            identities.add(identity)
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"source row {row_num}: {exc}") from exc
        writer.writerow(canonical)
        lineage.append({"source_row": row_num, "canonical_row": len(lineage) + 2,
                        "source_ref": entry["evidence_refs"][0]})
    if dataset == "transactions" and not lineage:
        raise ValueError("no transactions in source")
    return {
        "dataset": dataset, "source_format": kind, "source_sha256": digest,
        "mapping_sha256": plan_hash, "sheet_or_delimiter": opts,
        "rows": len(lineage), "lineage": lineage, "canonical_csv": output.getvalue(),
        "reviewed_mapping_not_authenticated": True,
        "source_ledger_complete_proven": False,
    }


def audit_from_sources(*, rule_path: str | Path,
                       transactions_source: str | Path,
                       settlements_source: str | Path,
                       transaction_plan: dict[str, Any],
                       settlement_plan: dict[str, Any],
                       source_system: str,
                       completeness: dict[str, bool],
                       controls: dict[str, Any] | None = None,
                       **approval_options: Any) -> dict[str, Any]:
    """Call the EXISTING Frictionless/readiness/HMAC/DB-gated CSV audit path."""
    txn = normalize_source(transactions_source, dataset="transactions",
                           source_system=source_system, plan=transaction_plan)
    credits = normalize_source(settlements_source, dataset="settlements",
                               source_system=source_system, plan=settlement_plan)
    with tempfile.TemporaryDirectory(prefix="lhfm-canonical-") as folder:
        t = Path(folder) / "transactions.csv"
        s = Path(folder) / "settlements.csv"
        t.write_text(txn["canonical_csv"], encoding="utf-8", newline="")
        s.write_text(credits["canonical_csv"], encoding="utf-8", newline="")
        report = audit_from_csv(
            rule_path, t, s, source_system=source_system,
            completeness=completeness, controls=controls,
            **approval_options,
        )
    report["source_lineage"] = [
        {k: v for k, v in item.items() if k != "canonical_csv"} for item in (txn, credits)
    ]
    report["normalization_verified"] = True
    return report
