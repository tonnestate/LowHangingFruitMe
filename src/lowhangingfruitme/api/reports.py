"""Minimal customer-facing export of an evidenced audit plus manual recovery ledger.

Only a curated report schema is exported. The original report and uploaded files
stay in private storage; no signatures, internal paths or tokens are serialized.
"""
from __future__ import annotations

from html import escape
import io
import json
from typing import Any


class ReportNotReady(ValueError):
    """Unreviewed / incomplete / unexecuted audits are not customer findings."""


def customer_case(run: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    report = run.get("report")
    if (run.get("status") != "COMPLETED"
            or run.get("audit_executed") is not True
            or not isinstance(report, dict)
            or report.get("status") != "EVIDENCED"
            or not isinstance(report.get("readiness"), dict)
            or report["readiness"].get("audit_admissible") is not True
            or not isinstance(ledger, dict)
            or ledger.get("audit_id") != run.get("audit_id")):
        raise ReportNotReady("final report requires an evidenced, authorized audit and its ledger")
    required = (
        "supplier_id", "agreement_id", "rule_id", "rule_revision",
        "period_start", "period_end", "currency", "difference_net",
        "expected_bonus_net", "recorded_bonus_net", "input_snapshot_sha256",
    )
    if any(not report.get(k) for k in required) or report["currency"] != "EUR":
        raise ReportNotReady("incomplete EUR evidence summary")
    if ledger.get("audited_difference_net") != report["difference_net"]:
        raise ReportNotReady("ledger and audited difference do not reconcile")
    if not isinstance(report.get("input_provenance"), dict):
        raise ReportNotReady("source provenance missing from this audit run")
    provenance = report["input_provenance"]
    for kind in ("transactions", "settlements", "contract"):
        section = provenance.get(kind)
        if not isinstance(section, dict) or not section.get("original_sha256"):
            raise ReportNotReady("a source SHA-256 digest is missing")
    # Fee proposal does not constitute an invoice or payment proof.
    if ledger.get("billing_authorized") is not False or ledger.get("invoice_created") is not False:
        raise ReportNotReady("unsupported billing state in MVP")
    for money in ("confirmed_realization_net", "fee_proposal_net", "fee_due_net"):
        if not isinstance(ledger.get(money), str):
            raise ReportNotReady("missing financial ledger field")
    return {
        "schema_version": "1.0",
        "audit_id": run["audit_id"],
        "audit_status": "EVIDENCED",
        "supplier_id": report["supplier_id"],
        "agreement_id": report["agreement_id"],
        "rule_id": report["rule_id"],
        "rule_revision": report["rule_revision"],
        "rule_evidence_refs": report.get("rule_evidence_refs", []),
        "period_start": report["period_start"],
        "period_end": report["period_end"],
        "currency": "EUR",
        "eligible_base_net": report.get("eligible_base_net"),
        "expected_bonus_net": report["expected_bonus_net"],
        "recorded_bonus_net": report["recorded_bonus_net"],
        "calculated_variance_net": report["difference_net"],
        "included_transactions": report.get("included_transactions", []),
        "matched_settlements": report.get("matched_settlements", []),
        "excluded_entries": report.get("excluded_entries", []),
        "input_snapshot_sha256": report["input_snapshot_sha256"],
        "source_provenance": {
            kind: {
                key: value for key in (
                    "original_sha256", "mapping_sha256", "rows", "upload_id",
                )
                if (value := provenance[kind].get(key)) is not None
            } for kind in ("transactions", "settlements", "contract")
        },
        "lineage_sha256": provenance.get("lineage_sha256"),
        "recovery": {
            "case_id": ledger.get("case_id"),
            "case_status": ledger.get("case_status", "NONE"),
            "case_status_reason": ledger.get("case_status_reason"),
            "confirmed_realization_net": ledger["confirmed_realization_net"],
            "fee_rate": "0.03",
            "fee_proposal_net": ledger["fee_proposal_net"],
            "billable_recovery_net": "0.00",
            "fee_due_net": ledger["fee_due_net"],
            "billing_authorized": False,
            "invoice_created": False,
            "finance_evidence_status": ledger.get("finance_evidence_status"),
            "events": [{
                "event_id": row.get("event_id"),
                "kind": row.get("kind"),
                "amount_net": row.get("amount_net"),
                "evidence_upload_id": row.get("evidence_upload_id"),
                "state": row.get("state"),
                "verified_by": row.get("verified_by"),
                "reverses_event_id": row.get("reverses_event_id"),
            } for row in ledger.get("events", [])],
        },
        "limitations": [
            "Rechnerische Differenz ist keine rechtlich festgestellte Forderung.",
            "ERP-Vollstaendigkeit nur gegen extern gelieferte Kontrollsummen und Erklaerungen plausibilisiert.",
            "Finanzpruefer-Bestaetigung ersetzt keinen unabhaengigen Banknachweis.",
            "3 Prozent sind nur ein unverbindlicher Honorarvorschlag; Rechnung und Zahlungsanspruch sind nicht freigegeben.",
            "Detaillierte Originaldatei-Zeilenreferenzen bleiben im privaten, hashgebundenen Lineage-Snapshot.",
        ],
    }


def _xlsx_text(value: Any) -> str:
    # Excel formula-injection prevention; display only, never executable code.
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + text
    return text


def render_export(case: dict[str, Any], fmt: str) -> tuple[bytes, str]:
    if fmt == "json":
        return (
            json.dumps(case, sort_keys=True, ensure_ascii=False, indent=2,
                       allow_nan=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )
    if fmt == "xlsx":
        from openpyxl import Workbook
        from openpyxl.styles import Font
        workbook = Workbook()
        summary = workbook.active
        summary.title = "Differenzfall"
        summary.append(["Merkmal", "Wert"])
        fields = {
            "Audit-ID": case["audit_id"],
            "Status": case["audit_status"],
            "Lieferant": case["supplier_id"],
            "Vertrag": case["agreement_id"],
            "Regel / Revision": case["rule_id"] + " / " + case["rule_revision"],
            "Zeitraum": case["period_start"] + " - " + case["period_end"],
            "Bonusbasis netto EUR": case["eligible_base_net"],
            "Erwarteter Bonus EUR": case["expected_bonus_net"],
            "Bereits verbucht EUR": case["recorded_bonus_net"],
            "Rechnerische Differenz EUR": case["calculated_variance_net"],
            "Fallstatus": case["recovery"]["case_status"],
            "Finanziell bestaetigte Realisierung EUR": case["recovery"]["confirmed_realization_net"],
            "Honorarvorschlag 3 Prozent EUR": case["recovery"]["fee_proposal_net"],
            "Abrechenbare Realisierung EUR": case["recovery"]["billable_recovery_net"],
            "Faelliges Honorar EUR": case["recovery"]["fee_due_net"],
            "Quellsnapshot SHA-256": case["input_snapshot_sha256"],
            "Lineage SHA-256": case["lineage_sha256"],
        }
        for name, value in fields.items():
            summary.append([_xlsx_text(name), _xlsx_text(value)])
        sources = workbook.create_sheet("Quellen")
        sources.append(["Datenart", "Original SHA-256", "Mapping SHA-256", "Upload-ID", "Zeilen"])
        for kind, prov in case["source_provenance"].items():
            sources.append([_xlsx_text(kind),
                            _xlsx_text(prov.get("original_sha256")),
                            _xlsx_text(prov.get("mapping_sha256")),
                            _xlsx_text(prov.get("upload_id")),
                            _xlsx_text(prov.get("rows"))])
        evidence = workbook.create_sheet("Evidenz")
        evidence.append(["Typ", "Referenz", "Anmerkung"])
        for key, typ in (("rule_evidence_refs", "Vertragsregel"),
                         ("included_transactions", "Bonusrelevanter Vorgang"),
                         ("matched_settlements", "Verrechnete Gutschrift")):
            for reference in case[key]:
                evidence.append([typ, _xlsx_text(reference),
                                 "Originalzeile in privater Lineage-Datei"])
        for row in case["excluded_entries"]:
            evidence.append(["Ausgeschlossen", _xlsx_text(row.get("entry")),
                             _xlsx_text(row.get("reason"))])
        events = workbook.create_sheet("Realisierungen")
        events.append(["Ereignis", "Art", "Betrag EUR", "Status", "Beleg-Upload", "Pruefer"])
        for row in case["recovery"]["events"]:
            events.append([_xlsx_text(row.get(k)) for k in (
                "event_id", "kind", "amount_net", "state",
                "evidence_upload_id", "verified_by",
            )])
        limits = workbook.create_sheet("Grenzen")
        limits.append(["Hinweis"])
        for note in case["limitations"]:
            limits.append([_xlsx_text(note)])
        for ws in workbook:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                cell.font = Font(bold=True)
            ws.column_dimensions["A"].width = 38
            ws.column_dimensions["B"].width = 57
            ws.column_dimensions["C"].width = 52
            ws.column_dimensions["D"].width = 37
            ws.column_dimensions["E"].width = 30
            ws.column_dimensions["F"].width = 35
        output = io.BytesIO()
        workbook.save(output)
        return output.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if fmt == "pdf":
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        )
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=17*mm,
                                leftMargin=17*mm, topMargin=17*mm,
                                bottomMargin=17*mm, title="LowHangingFruitMe Differenzfall")
        regular = ParagraphStyle("Body", fontName="Helvetica", fontSize=9,
                                 leading=13, alignment=TA_LEFT, spaceAfter=4)
        heading = ParagraphStyle("Heading", parent=regular, fontSize=17,
                                 leading=23, spaceAfter=12)
        section = ParagraphStyle("Section", parent=regular, fontSize=11,
                                 leading=16, spaceBefore=11, spaceAfter=6)
        para = lambda s: Paragraph(escape(str(s)), regular)
        story = [Paragraph("LowHangingFruitMe - belegter Differenzfall", heading),
                 para("Audit-ID: " + case["audit_id"]),
                 para("Lieferant: " + case["supplier_id"] +
                      " | Vertrag: " + case["agreement_id"]),
                 para("Pruefzeitraum: " + case["period_start"] + " bis " +
                      case["period_end"] + " | Regelrevision: " + case["rule_revision"]),
                 Spacer(1, 5*mm)]
        vals = [
            ("Bonusfaehige Basis", case["eligible_base_net"]),
            ("Erwarteter Bonus", case["expected_bonus_net"]),
            ("Erfasste Gutschriften", case["recorded_bonus_net"]),
            ("Rechnerische Differenz", case["calculated_variance_net"]),
            ("Fallstatus", case["recovery"]["case_status"]),
            ("Bestaetigte Realisierung", case["recovery"]["confirmed_realization_net"]),
            ("Honorarvorschlag (3 %)", case["recovery"]["fee_proposal_net"]),
            ("Abrechenbarer Betrag", case["recovery"]["billable_recovery_net"]),
            ("Faelliges Honorar", case["recovery"]["fee_due_net"]),
        ]
        tab = Table([[para(k), para(str(v) + " EUR")] for k, v in vals],
                    colWidths=[100*mm, 60*mm], hAlign="LEFT")
        tab.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LINEBELOW", (0,3), (-1,3), 0.8, colors.black),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ]))
        story.append(tab)
        story.append(Paragraph("Quellen und Pruefbelege", section))
        story.append(para("Original-Snapshot: " + case["input_snapshot_sha256"]))
        for kind, item in case["source_provenance"].items():
            story.append(para(kind + ": sha256:" + item["original_sha256"]))
        if case["lineage_sha256"]:
            story.append(para("Zeilenreferenz-Register: sha256:" + case["lineage_sha256"]))
        story.append(para("Beruecksichtigte Transaktionen: " +
                          ", ".join(map(str, case["included_transactions"][:50]))))
        story.append(para("Zugeordnete Gutschriften: " +
                          ", ".join(map(str, case["matched_settlements"][:50]))))
        if len(case["included_transactions"]) > 50 or len(case["matched_settlements"]) > 50:
            story.append(para("Weitere Belegreferenzen: vollstaendig im JSON/XLSX-Export."))
        story.append(Paragraph("Einordnung und Grenzen", section))
        for item in case["limitations"]:
            story.append(para("- " + item))
        doc.build(story)
        return output.getvalue(), "application/pdf"
    raise ValueError("unsupported export format")
