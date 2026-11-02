"""Deterministic, fail-closed data-readiness assessment for supplier bonus audits.

'READY_FOR_AUDIT' means the imported snapshot matches *provided* external
control reports. It NEVER proves the customer's ERP export is complete.
No LLM use, no monetary claim, no billing.
"""
from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import json
from typing import Any

from .rebate import BonusRule, Entry, _decimal

CONTROL_KEYS = frozenset(("source_system", "supplier_id", "agreement_id", "period_start",
                          "period_end", "transactions", "settlements"))
SUMMARY_KEYS = frozenset(("row_count", "net_total", "source_reference"))
FLAGS = frozenset(("transactions_complete", "settlements_complete", "agreements_complete"))


def _issue(code: str, field: str, severity: str, explanation: str) -> dict[str, str]:
    return {"code": code, "field": field, "severity": severity, "explanation": explanation}


def _control_section(section: Any, name: str) -> tuple[int, Decimal, str]:
    if not isinstance(section, dict) or set(section) != SUMMARY_KEYS:
        raise ValueError(f"{name}: expected row_count, net_total and source_reference")
    number = section["row_count"]
    if type(number) is not int or number < 0:
        raise ValueError(f"{name}.row_count must be nonnegative integer")
    total = _decimal(section["net_total"], name + ".net_total")
    if total != total.quantize(Decimal("0.01")):
        raise ValueError(f"{name}.net_total must have at most two decimal places")
    reference = section["source_reference"]
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError(f"{name}.source_reference must identify the separate source report")
    return number, total, reference.strip()


def assess_readiness(
    rule_raw: dict[str, Any],
    transaction_rows: list[dict[str, Any]],
    settlement_rows: list[dict[str, Any]],
    completeness: dict[str, bool],
    controls: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assess one-supplier/one-agreement/one-period technical input readiness.

    Controls must come from a separate customer-authorized ERP/accounting
    control report. The code checks consistency against provided totals, not
    authenticity or completeness of that originating source.
    """
    rule = BonusRule.load(rule_raw)
    if type(completeness) is not dict or set(completeness) != FLAGS or any(
        type(v) is not bool for v in completeness.values()
    ):
        raise ValueError("three explicit boolean completeness assertions required")
    if type(transaction_rows) is not list or type(settlement_rows) is not list:
        raise ValueError("transactions and settlements must be lists")
    transactions = [Entry.load(row) for row in transaction_rows]
    settlements = [Entry.load(row, settlement=True) for row in settlement_rows]
    issues: list[dict[str, str]] = []
    summary: dict[str, dict[str, str | int | bool | None]] = {}

    if not rule.approved:
        issues.append(_issue("RULE_NOT_APPROVED", "rule.approved", "BLOCKER",
                             "Contract rule must be approved before an audit"))
    if not rule.evidence_refs:
        issues.append(_issue("RULE_SOURCE_MISSING", "rule.evidence_refs", "BLOCKER",
                             "Provide a contract clause/page source reference"))
    for key in sorted(FLAGS):
        if not completeness[key]:
            issues.append(_issue("SOURCE_COMPLETENESS_NOT_ATTESTED", key, "WARNING",
                                 "Operator/customer did not attest this source as complete"))
    if controls is None:
        issues.append(_issue("SOURCE_CONTROLS_MISSING", "controls", "WARNING",
                             "Upload separate ERP control totals for both datasets"))
    elif not isinstance(controls, dict) or set(controls) != CONTROL_KEYS:
        raise ValueError("controls must contain source_system, supplier_id, agreement_id, "
                         "period_start, period_end, transactions and settlements")
    else:
        expected_scope = {
            "supplier_id": rule.supplier_id,
            "agreement_id": rule.agreement_id,
            "period_start": rule.period_start.isoformat(),
            "period_end": rule.period_end.isoformat(),
        }
        for key, value in expected_scope.items():
            if controls[key] != value:
                issues.append(_issue("CONTROL_SCOPE_MISMATCH", "controls." + key, "BLOCKER",
                                     f"Control scope differs from approved agreement on {key}"))
        if not isinstance(controls["source_system"], str) or not controls["source_system"].strip():
            raise ValueError("controls.source_system must be a nonempty string")

    for name, entries in (("transactions", transactions), ("settlements", settlements)):
        nonposted = [e for e in entries if not e.posted]
        mixed = [e for e in entries if e.supplier_id != rule.supplier_id or e.currency != rule.currency]
        out_of_scope = (
            [e for e in entries if e.basis != rule.basis or not rule.period_start <= e.date <= rule.period_end]
            if name == "transactions" else
            [e for e in entries if (e.agreement_id != rule.agreement_id or
                                    e.period_start != rule.period_start or
                                    e.period_end != rule.period_end)]
        )
        if mixed:
            issues.append(_issue("MIXED_SUPPLIER_OR_CURRENCY", name, "BLOCKER",
                                 "Canonical v0.3 import permits a single supplier and EUR currency"))
        if nonposted:
            issues.append(_issue("UNPOSTED_INPUT_ROWS", name, "BLOCKER",
                                 "Remove or explicitly reconcile unposted source records"))
        if out_of_scope:
            issues.append(_issue("UNALLOCATED_OR_OUTSIDE_SCOPE", name, "BLOCKER",
                                 "Resolve rows outside the agreed transaction or settlement scope"))
        if name == "transactions" and not entries:
            issues.append(_issue("NO_PURCHASE_ROWS", name, "BLOCKER",
                                 "No purchasing basis for the specified supplier and period"))
        if any(not e.evidence_refs for e in entries):
            issues.append(_issue("ENTRY_SOURCE_MISSING", name, "BLOCKER",
                                 "Each entry must include a source reference"))
        keys = [(e.source_system, e.external_id) for e in entries]
        if len(set(keys)) != len(keys):
            issues.append(_issue("DUPLICATE_SOURCE_IDS", name, "BLOCKER",
                                 "Resolve duplicate source system/external IDs"))
        actual_total = sum((e.amount for e in entries), Decimal("0.00"))
        section: dict[str, str | int | bool | None] = {
            "actual_rows": len(entries),
            "actual_net_total": str(actual_total.quantize(Decimal("0.01"))),
            "expected_rows": None, "expected_net_total": None,
            "control_reference": None, "matched": False,
        }
        if controls is not None:
            count, amount, reference = _control_section(controls[name], name)
            section.update(expected_rows=count, expected_net_total=str(amount),
                           control_reference=reference,
                           matched=(count == len(entries) and amount == actual_total))
            if count != len(entries):
                issues.append(_issue("ROW_COUNT_MISMATCH", name + ".row_count", "BLOCKER",
                                     f"{len(entries)} imported rows vs {count} in supplied control report"))
            if amount != actual_total:
                issues.append(_issue("NET_TOTAL_MISMATCH", name + ".net_total", "BLOCKER",
                                     "Imported net sum differs from supplied source control total"))
            if any(e.source_system != controls["source_system"] for e in entries):
                issues.append(_issue("SOURCE_SYSTEM_MISMATCH", name, "BLOCKER",
                                     "Imported entry source differs from supplied control source"))
        summary[name] = section

    statuses = {issue["severity"] for issue in issues}
    status = ("NOT_READY" if "BLOCKER" in statuses else
              "LIMITED" if "WARNING" in statuses else "READY_FOR_AUDIT")
    evidence = {
        "rule_revision": rule.revision,
        "rule_id": rule.rule_id,
        "agreement_id": rule.agreement_id,
        "supplier_id": rule.supplier_id,
        "period_start": rule.period_start.isoformat(),
        "period_end": rule.period_end.isoformat(),
        "controls": controls,
        "checks": summary,
        "completeness": completeness,
    }
    digest = sha256(json.dumps(evidence, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False).encode()).hexdigest()
    return {
        "gate_version": "0.3.0",
        "status": status, "audit_admissible": status == "READY_FOR_AUDIT",
        "issues": issues, "reconciliation": summary, "gate_snapshot_sha256": digest,
        "control_origin": "customer_or_operator_supplied_unverified",
        "external_ledger_completeness_proven": False,
        "automated_percentage_score": None,
    }
