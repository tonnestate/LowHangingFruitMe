"""Universal import regression: arbitrary source columns, explicit mapping and provenance."""
from copy import deepcopy
import csv
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
import os
from uuid import uuid4
from datetime import datetime, timezone

from lowhangingfruitme.universal_import import (
    inspect_source, normalize_source, audit_from_sources,
)
from lowhangingfruitme.approval import issue_approval
from lowhangingfruitme.approval_registry import ApprovalRegistry

ROOT = Path(__file__).parent / "fixtures"
RULE = json.loads((ROOT / "rule.json").read_text(encoding="utf-8"))
CONTROLS = json.loads((ROOT / "source_controls.json").read_text(encoding="utf-8"))
TX_MAP = {
    "external_id": "Belegnummer", "supplier_id": "Kreditor",
    "date": "Belegdatum", "amount_net": "Nettobetrag",
    "posted": "Gebucht", "kind": "Belegart",
}
SETTLE_MAP = {
    "external_id": "Belegnummer", "supplier_id": "Kreditor",
    "date": "Belegdatum", "amount_net": "Nettobetrag",
    "posted": "Gebucht", "kind": "Belegart", "agreement_id": "Vertragsnr",
    "period_start": "Bonus_von", "period_end": "Bonus_bis",
}


def plan(file: Path, dataset: str, mapping: dict, *, sheet=None):
    return {
        "source_sha256": sha256(file.read_bytes()).hexdigest(),
        "dataset": dataset, "mapping": mapping,
        "constants": {"currency": "EUR", "basis": "INVOICE"}
            if dataset == "transactions" else {"currency": "EUR"},
        "sheet_name": sheet, "decimal_format": "DE",
        "date_format": "DE", "boolean_format": "DE",
        "reviewed_by": "synthetic-test-reviewer", "confirmed": True,
    }


class UniversalMappingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.txn = self.root / "Einkauf.csv"
        self.txn.write_text(
            "Belegnummer;Kreditor;Belegdatum;Nettobetrag;Gebucht;Belegart;Zusatzinfo\n"
            "INV-001;SUP-1;10.05.2025;210.000,00;Ja;PURCHASE;unmapped\n"
            "RET-001;SUP-1;10.07.2025;-10.000,00;Ja;RETURN;unmapped\n",
            encoding="utf-8",
        )
        self.credits = self.root / "Gutschriften.csv"
        self.credits.write_text(
            "Belegnummer;Kreditor;Belegdatum;Nettobetrag;Gebucht;Belegart;Vertragsnr;Bonus_von;Bonus_bis\n"
            "CREDIT-001;SUP-1;15.01.2026;1.500,00;Ja;CREDIT;AGR-1;01.01.2025;31.12.2025\n",
            encoding="utf-8",
        )

    def test_inspect_proposes_mapping_but_cannot_approve(self):
        info = inspect_source(self.txn, dataset="transactions")
        self.assertEqual(info["format"], "CSV_TABLE")
        self.assertEqual(info["rows"], 2)
        self.assertEqual(info["proposed_mapping"]["external_id"], ["Belegnummer"])
        self.assertEqual(info["proposed_mapping"]["amount_net"], ["Nettobetrag"])
        self.assertFalse(info["audit_ready"])
        self.assertFalse(info["normalized"])
        self.assertIn("Zusatzinfo", info["unmatched_columns"])

    def test_explicit_mapping_normalizes_de_amount_and_dates(self):
        mapping = plan(self.txn, "transactions", TX_MAP)
        output = normalize_source(self.txn, dataset="transactions",
                                  source_system="erp", plan=mapping)
        self.assertEqual(output["rows"], 2)
        reader = csv.DictReader(output["canonical_csv"].splitlines())
        rows = list(reader)
        self.assertEqual(rows[0]["amount_net"], "210000.00")
        self.assertEqual(rows[1]["amount_net"], "-10000.00")
        self.assertEqual(rows[0]["date"], "2025-05-10")
        self.assertEqual(rows[0]["posted"], "true")
        self.assertEqual(output["lineage"][0]["source_row"], 2)
        self.assertIn(output["source_sha256"], output["lineage"][1]["source_ref"])
        self.assertFalse(output["source_ledger_complete_proven"])

    def test_settlement_with_explicit_period_normalizes(self):
        output = normalize_source(self.credits, dataset="settlements",
                                  source_system="erp",
                                  plan=plan(self.credits, "settlements", SETTLE_MAP))
        record = list(csv.DictReader(output["canonical_csv"].splitlines()))[0]
        self.assertEqual(record["period_start"], "2025-01-01")
        self.assertEqual(record["period_end"], "2025-12-31")
        self.assertEqual(record["amount_net"], "1500.00")

    def test_changed_file_hash_prevents_reusing_mapping(self):
        p = plan(self.txn, "transactions", TX_MAP)
        self.txn.write_text(self.txn.read_text() + "OTHER;SUP-1;11.07.2025;1,00;Ja;PURCHASE;x\n")
        with self.assertRaisesRegex(ValueError, "bound to this exact"):
            normalize_source(self.txn, dataset="transactions", source_system="erp", plan=p)

    def test_unreviewed_mapping_rejected(self):
        p = plan(self.txn, "transactions", TX_MAP)
        p["confirmed"] = False
        with self.assertRaisesRegex(ValueError, "reviewer confirmation"):
            normalize_source(self.txn, dataset="transactions", source_system="erp", plan=p)

    def test_missing_posted_source_never_assumed_true(self):
        p = plan(self.txn, "transactions", TX_MAP)
        del p["mapping"]["posted"]
        p["constants"]["posted"] = "true"
        with self.assertRaisesRegex(ValueError, "source columns"):
            normalize_source(self.txn, dataset="transactions", source_system="erp", plan=p)

    def test_missing_settlement_contract_never_implied(self):
        p = plan(self.credits, "settlements", SETTLE_MAP)
        del p["mapping"]["agreement_id"]
        p["constants"]["agreement_id"] = "AGR-1"
        with self.assertRaisesRegex(ValueError, "source columns"):
            normalize_source(self.credits, dataset="settlements", source_system="erp", plan=p)

    def test_wrong_decimal_locale_not_guessed(self):
        p = plan(self.txn, "transactions", TX_MAP)
        p["decimal_format"] = "DOT"
        with self.assertRaisesRegex(ValueError, "invalid dot decimal"):
            normalize_source(self.txn, dataset="transactions", source_system="erp", plan=p)

    def test_ambiguous_synonyms_are_proposed_as_multiple(self):
        self.txn.write_text(
            "Belegnummer;invoice_number;Kreditor;Belegdatum;Nettobetrag;Gebucht;Belegart\n"
            "1;2;SUP-1;10.05.2025;100,00;Ja;PURCHASE\n", encoding="utf-8",
        )
        info = inspect_source(self.txn, dataset="transactions")
        self.assertEqual(len(info["proposed_mapping"]["external_id"]), 2)
        self.assertFalse(info["audit_ready"])

    def test_duplicate_case_insensitive_headers_rejected(self):
        self.txn.write_text("Belegnummer;belegnummer\n1;2\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate case"):
            inspect_source(self.txn, dataset="transactions")

    def test_pdf_is_document_route_only(self):
        pdf = self.root / "contract.pdf"
        pdf.write_bytes(b"%PDF-1.7\n%synthetic not a parseable PDF")
        info = inspect_source(pdf)
        self.assertEqual(info["route"], "document_pdf")
        self.assertFalse(info["normalized"])
        with self.assertRaisesRegex(ValueError, "only CSV/XLSX"):
            normalize_source(pdf, dataset="transactions",
                             source_system="erp", plan={})

    def test_xml_recognition_only_not_posted_ledger(self):
        xml = self.root / "e-rechnung.xml"
        xml.write_text(
            '<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">'
            '<ID>INV-1</ID></Invoice>', encoding="utf-8",
        )
        info = inspect_source(xml)
        self.assertEqual(info["route"], "einvoice_xml_review")
        self.assertFalse(info["audit_ready"])

    def test_xml_external_entities_blocked(self):
        xml = self.root / "danger.xml"
        xml.write_text(
            '<!DOCTYPE Invoice [<!ENTITY attacker SYSTEM "file:///etc/passwd">]>'
            '<Invoice>&attacker;</Invoice>', encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            inspect_source(xml)

    def test_xlsx_preview_and_normalization(self):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "ERP_Export"
        ws.append(list(TX_MAP.values()))
        ws.append(["INV-001", "SUP-1", "10.05.2025", "210.000,00", "Ja", "PURCHASE"])
        ws.append(["RET-001", "SUP-1", "10.07.2025", "-10.000,00", "Ja", "RETURN"])
        excel = self.root / "ERP.xlsx"
        wb.save(excel)
        info = inspect_source(excel, dataset="transactions", sheet_name="ERP_Export")
        self.assertEqual(info["format"], "XLSX_TABLE")
        self.assertEqual(info["rows"], 2)
        output = normalize_source(excel, dataset="transactions", source_system="erp",
                                  plan=plan(excel, "transactions", TX_MAP,
                                            sheet="ERP_Export"))
        self.assertEqual(output["rows"], 2)
        self.assertEqual(output["sheet_or_delimiter"]["sheet"], "ERP_Export")

    def test_xlsx_formula_blocked(self):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append(list(TX_MAP.values()))
        ws.append(["INV-001", "SUP-1", "10.05.2025", "=100+1", "Ja", "PURCHASE"])
        excel = self.root / "ERP.xlsx"
        wb.save(excel)
        with self.assertRaisesRegex(ValueError, "formulas"):
            inspect_source(excel, dataset="transactions")

    def test_xlsx_multisheet_explicit_selection(self):
        from openpyxl import Workbook
        wb = Workbook()
        wb.active.append(list(TX_MAP.values()))
        wb.create_sheet("Other")
        excel = self.root / "ERP.xlsx"
        wb.save(excel)
        with self.assertRaisesRegex(ValueError, "multiple sheets"):
            inspect_source(excel, dataset="transactions")


@unittest.skipUnless(bool(os.environ.get("LHFM_DB_HOST")), "real MariaDB required")
class UniversalFullAuditTests(UniversalMappingTests):
    def test_normalized_sources_reuse_canonical_financial_gate(self):
        key = b"synthetic-universal-integration-key-32"
        rule_path = self.root / "rule.json"
        rule_path.write_text(json.dumps(RULE), encoding="utf-8")
        doc = self.root / "synthetic_contract.txt"
        doc.write_text("NOT A REAL CONTRACT", encoding="utf-8")
        doc_hash = sha256(doc.read_bytes()).hexdigest()
        receipt = issue_approval(
            RULE, key=key, tenant_id="T-SYN-1", legal_entity_id="LE-SYN-1",
            reviewer_id="REVIEWER-SYN-1", approval_id="UNI-" + uuid4().hex,
            source_revision_id="REV-1", document_sha256=doc_hash,
            approved_at=datetime.now(timezone.utc),
        )
        registry = ApprovalRegistry.from_environment()
        registry.register(receipt, rule=RULE, key=key,
                          document_sha256=doc_hash, tenant_id="T-SYN-1",
                          legal_entity_id="LE-SYN-1",
                          authenticated_actor_id="REVIEWER-SYN-1")
        controls = deepcopy(CONTROLS)
        report = audit_from_sources(
            rule_path=rule_path, transactions_source=self.txn,
            settlements_source=self.credits,
            transaction_plan=plan(self.txn, "transactions", TX_MAP),
            settlement_plan=plan(self.credits, "settlements", SETTLE_MAP),
            source_system="erp",
            controls=controls,
            completeness={"transactions_complete": True,
                          "settlements_complete": True,
                          "agreements_complete": True},
            approval_receipt=receipt, approval_key=key,
            approval_scope={"tenant_id": "T-SYN-1", "legal_entity_id": "LE-SYN-1"},
            contract_source_path=doc, approval_registry=registry,
        )
        self.assertTrue(report["audit_executed"])
        self.assertEqual(report["status"], "EVIDENCED")
        self.assertEqual(report["difference_net"], "2500.00")
        self.assertEqual(report["fee_due_net"], "0.00")
        self.assertEqual(report["source_lineage"][0]["source_sha256"],
                         sha256(self.txn.read_bytes()).hexdigest())
        self.assertEqual(report["source_lineage"][0]["lineage"][0]["canonical_row"], 2)


if __name__ == "__main__":
    unittest.main()
