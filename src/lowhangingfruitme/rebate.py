"""Deterministic, source-evidenced supplier rebate calculations.

No LLMs, network, tenant store, legal claim assessments or economic-recovery inference.
Amounts and rates are strictly Decimal, never binary floating point.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable


class AuditStatus(str, Enum):
    EVIDENCED = "EVIDENCED"  # data-reconciliation evidence, NOT legally confirmed
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_CALCULABLE = "NOT_CALCULABLE"


class RuleKind(str, Enum):
    FLAT_RATE = "FLAT_RATE"
    RETROACTIVE_FULL_BASE = "RETROACTIVE_FULL_BASE"
    MARGINAL_PER_TIER = "MARGINAL_PER_TIER"
    FIXED_THRESHOLD_REWARD = "FIXED_THRESHOLD_REWARD"


class EntryKind(str, Enum):
    PURCHASE = "PURCHASE"
    RETURN = "RETURN"
    CREDIT = "CREDIT"
    REVERSAL = "REVERSAL"


def _decimal(value: Any, name: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{name}: use a decimal string, never a float or boolean")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{name}: invalid decimal") from exc
    if not amount.is_finite():
        raise ValueError(f"{name}: must be finite")
    return amount


def _money(value: Decimal, scale: Decimal = Decimal("0.01")) -> Decimal:
    return value.quantize(scale, rounding=ROUND_HALF_UP)


def _date(value: str, name: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: expected ISO date YYYY-MM-DD") from exc


def _required_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: non-empty string required")
    return value.strip()


def _evidence(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        raise ValueError(f"{name}: list of non-empty source references required")
    return tuple(value)


def _boolean(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name}: boolean required")
    return value


@dataclass(frozen=True)
class Tier:
    threshold: Decimal
    rate: Decimal | None = None
    reward: Decimal | None = None

    @classmethod
    def load(cls, raw: dict[str, Any], kind: RuleKind) -> Tier:
        threshold = _decimal(raw.get("threshold"), "threshold")
        if threshold < 0:
            raise ValueError("threshold must be >= 0")
        if kind == RuleKind.FIXED_THRESHOLD_REWARD:
            if "rate" in raw:
                raise ValueError("fixed threshold tier must not specify rate")
            reward = _decimal(raw.get("reward"), "reward")
            if reward < 0:
                raise ValueError("reward must be >= 0")
            return cls(threshold, reward=reward)
        if "reward" in raw:
            raise ValueError("percentage tier must not specify reward")
        rate = _decimal(raw.get("rate"), "rate")
        if not Decimal("0") <= rate <= Decimal("1"):
            raise ValueError("tier rate must be between 0 and 1")
        return cls(threshold, rate=rate)


@dataclass(frozen=True)
class BonusRule:
    rule_id: str
    revision: str
    kind: RuleKind
    supplier_id: str
    agreement_id: str
    currency: str
    period_start: date
    period_end: date
    basis: str
    rate: Decimal | None
    tiers: tuple[Tier, ...]
    approved: bool
    evidence_refs: tuple[str, ...]

    @classmethod
    def load(cls, raw: dict[str, Any]) -> BonusRule:
        kind = RuleKind(raw["kind"])
        rate = _decimal(raw["rate"], "rate") if "rate" in raw else None
        tiers = tuple(Tier.load(t, kind) for t in raw.get("tiers", []))
        if kind == RuleKind.FLAT_RATE:
            if rate is None or not Decimal("0") <= rate <= Decimal("1") or tiers:
                raise ValueError("flat rate requires 0 <= rate <= 1 and no tiers")
        elif rate is not None or not tiers:
            raise ValueError("tiered rule requires tiers, without flat rate")
        thresholds = [t.threshold for t in tiers]
        if thresholds != sorted(set(thresholds)):
            raise ValueError("tier thresholds must be strictly increasing")
        start, end = _date(raw["period_start"], "period_start"), _date(raw["period_end"], "period_end")
        if start > end:
            raise ValueError("period_start must be <= period_end")
        currency = _required_str(raw.get("currency"), "currency")
        if currency != "EUR":
            raise ValueError("v0.1 supports EUR only; FX must not be inferred")
        basis = _required_str(raw.get("basis"), "basis")
        if basis not in ("INVOICE", "GOODS_RECEIPT"):
            raise ValueError("basis must be INVOICE or GOODS_RECEIPT")
        return cls(
            rule_id=_required_str(raw.get("rule_id"), "rule_id"),
            revision=_required_str(raw.get("revision"), "revision"),
            kind=kind,
            supplier_id=_required_str(raw.get("supplier_id"), "supplier_id"),
            agreement_id=_required_str(raw.get("agreement_id"), "agreement_id"),
            currency=currency, period_start=start, period_end=end, basis=basis,
            rate=rate, tiers=tiers,
            approved=_boolean(raw.get("approved"), "approved"),
            evidence_refs=_evidence(raw.get("evidence_refs"), "evidence_refs"),
        )


@dataclass(frozen=True)
class Entry:
    source_system: str
    external_id: str
    supplier_id: str
    date: date
    currency: str
    amount: Decimal
    kind: EntryKind
    posted: bool
    evidence_refs: tuple[str, ...]
    basis: str | None = None
    agreement_id: str | None = None
    period_start: date | None = None
    period_end: date | None = None

    @classmethod
    def load(cls, raw: dict[str, Any], settlement: bool = False) -> Entry:
        kind = EntryKind(raw["kind"])
        allowed = (EntryKind.CREDIT, EntryKind.REVERSAL) if settlement else (EntryKind.PURCHASE, EntryKind.RETURN)
        if kind not in allowed:
            raise ValueError(f"entry kind {kind.value} invalid for this dataset")
        amount = _decimal(raw.get("amount_net"), "amount_net")
        if kind in (EntryKind.PURCHASE, EntryKind.CREDIT) and amount <= 0:
            raise ValueError(f"{kind.value} must have positive amount_net")
        if kind in (EntryKind.RETURN, EntryKind.REVERSAL) and amount >= 0:
            raise ValueError(f"{kind.value} must have negative amount_net")
        basis = raw.get("basis")
        if not settlement and basis not in ("INVOICE", "GOODS_RECEIPT"):
            raise ValueError("purchase entry requires recognized basis")
        if settlement and basis is not None:
            raise ValueError("settlement entry must not specify purchase basis")
        start = _date(raw["period_start"], "period_start") if raw.get("period_start") is not None else None
        end = _date(raw["period_end"], "period_end") if raw.get("period_end") is not None else None
        if settlement and ((start is None) != (end is None)):
            raise ValueError("settlement period_start and period_end must appear together")
        if start and end and start > end:
            raise ValueError("settlement period start after end")
        return cls(
            source_system=_required_str(raw.get("source_system"), "source_system"),
            external_id=_required_str(raw.get("external_id"), "external_id"),
            supplier_id=_required_str(raw.get("supplier_id"), "supplier_id"),
            date=_date(raw.get("date"), "date"),
            currency=_required_str(raw.get("currency"), "currency"), amount=amount,
            kind=kind, posted=_boolean(raw.get("posted"), "posted"),
            evidence_refs=_evidence(raw.get("evidence_refs"), "evidence_refs"),
            basis=basis, agreement_id=raw.get("agreement_id"),
            period_start=start, period_end=end,
        )


def _unique(items: Iterable[Entry], dataset: str) -> list[Entry]:
    seen: dict[tuple[str, str], Entry] = {}
    for item in items:
        key = item.source_system, item.external_id
        if key in seen:
            if seen[key] != item:
                raise ValueError(f"conflicting {dataset} external identity: {key}")
            continue  # an exact repeated payload is idempotent
        seen[key] = item
    return sorted(seen.values(), key=lambda e: (e.source_system, e.external_id))


def _computed_bonus(rule: BonusRule, base: Decimal) -> Decimal:
    if base < 0:
        raise ValueError("eligible base is negative; source data requires review")
    if rule.kind == RuleKind.FLAT_RATE:
        assert rule.rate is not None
        return _money(base * rule.rate)
    if rule.kind == RuleKind.RETROACTIVE_FULL_BASE:
        applicable = [t for t in rule.tiers if base >= t.threshold]
        return _money(base * applicable[-1].rate) if applicable else Decimal("0.00")
    if rule.kind == RuleKind.FIXED_THRESHOLD_REWARD:
        applicable = [t for t in rule.tiers if base >= t.threshold]
        return _money(applicable[-1].reward) if applicable else Decimal("0.00")
    total = Decimal("0")
    for index, tier in enumerate(rule.tiers):
        cap = rule.tiers[index + 1].threshold if index + 1 < len(rule.tiers) else base
        eligible_in_band = max(Decimal("0"), min(base, cap) - tier.threshold)
        total += eligible_in_band * tier.rate
    return _money(total)


def _encode(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_encode(v) for v in value]
    if isinstance(value, dict):
        return {k: _encode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_encode(v) for v in value]
    raise TypeError(f"not serializable: {type(value)}")


def _digest(obj: dict[str, Any]) -> str:
    return sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def audit(payload: dict[str, Any]) -> dict[str, Any]:
    """Calculate an auditable, limited-scope supplier rebate reconciliation.

    Input is a verified data snapshot, NOT a claim that input data are complete.
    This function performs no network/disk changes, ERP writes or fee billing.
    """
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    rule = BonusRule.load(payload["rule"])
    if type(payload.get("transactions")) is not list or type(payload.get("settlements")) is not list:
        raise ValueError("transactions and settlements must be arrays")
    txns = _unique((Entry.load(x) for x in payload["transactions"]), "transaction")
    credits = _unique((Entry.load(x, settlement=True) for x in payload["settlements"]), "settlement")
    flags = payload.get("completeness", {})
    if type(flags) is not dict:
        raise ValueError("completeness must be an object")
    confirmed_txns = _boolean(flags.get("transactions_complete"), "transactions_complete")
    confirmed_credits = _boolean(flags.get("settlements_complete"), "settlements_complete")
    confirmed_amendments = _boolean(flags.get("agreements_complete"), "agreements_complete")
    included: list[str] = []
    matched: list[str] = []
    excluded: list[dict[str, str]] = []
    warnings: set[str] = set()
    blocking: set[str] = set()
    missing_evidence = not rule.evidence_refs
    eligible_base = Decimal("0")
    recorded = Decimal("0")

    # This low-level calculator does not authenticate the reviewer.
    # Full evidence status can only be granted by the signed intake gate.
    warnings.add("UNVERIFIED_APPROVAL_CONTEXT")
    if not rule.approved:
        warnings.add("RULE_NOT_APPROVED")
    if not confirmed_txns:
        warnings.add("TRANSACTIONS_INCOMPLETE")
    if not confirmed_credits:
        warnings.add("SETTLEMENTS_INCOMPLETE")
    if not confirmed_amendments:
        warnings.add("AGREEMENTS_INCOMPLETE")
    for entry in txns:
        key = f"{entry.source_system}:{entry.external_id}"
        if entry.supplier_id != rule.supplier_id:
            excluded.append({"entry": key, "reason": "OTHER_SUPPLIER"})
        elif entry.currency != rule.currency:
            blocking.add("MIXED_CURRENCY")
            excluded.append({"entry": key, "reason": "OTHER_CURRENCY"})
        elif entry.basis != rule.basis:
            excluded.append({"entry": key, "reason": "OTHER_BASIS"})
        elif not rule.period_start <= entry.date <= rule.period_end:
            excluded.append({"entry": key, "reason": "OUTSIDE_PERIOD"})
        elif not entry.posted:
            excluded.append({"entry": key, "reason": "NOT_POSTED"})
        else:
            eligible_base += entry.amount
            included.append(key)
            missing_evidence |= not entry.evidence_refs
    for entry in credits:
        key = f"{entry.source_system}:{entry.external_id}"
        if entry.supplier_id != rule.supplier_id:
            excluded.append({"entry": key, "reason": "OTHER_SUPPLIER"})
        elif entry.currency != rule.currency:
            blocking.add("MIXED_CURRENCY")
            excluded.append({"entry": key, "reason": "OTHER_CURRENCY"})
        elif not entry.posted:
            excluded.append({"entry": key, "reason": "NOT_POSTED"})
        elif entry.agreement_id == rule.agreement_id and entry.period_start == rule.period_start and entry.period_end == rule.period_end:
            recorded += entry.amount
            matched.append(key)
            missing_evidence |= not entry.evidence_refs
        elif entry.agreement_id is None or entry.period_start is None:
            warnings.add("UNALLOCATED_SETTLEMENT")
            excluded.append({"entry": key, "reason": "UNALLOCATED_SETTLEMENT"})
        else:
            excluded.append({"entry": key, "reason": "OTHER_AGREEMENT_OR_PERIOD"})
    if eligible_base < 0:
        blocking.add("NEGATIVE_ELIGIBLE_BASE")
    if recorded < 0:
        blocking.add("NEGATIVE_RECORDED_SETTLEMENT")
    if not included:
        warnings.add("NO_ELIGIBLE_TRANSACTIONS")
    if missing_evidence:
        warnings.add("MISSING_SOURCE_EVIDENCE")
    expected: Decimal | None = None
    difference: Decimal | None = None
    if not blocking:
        expected = _computed_bonus(rule, eligible_base)
        difference = _money(expected - recorded)
    status = (AuditStatus.NOT_CALCULABLE if blocking else
              AuditStatus.REVIEW_REQUIRED if warnings else AuditStatus.EVIDENCED)
    normalized_rule = {
        "rule_id": rule.rule_id, "revision": rule.revision, "kind": rule.kind.value,
        "supplier_id": rule.supplier_id, "agreement_id": rule.agreement_id,
        "currency": rule.currency, "period_start": rule.period_start.isoformat(),
        "period_end": rule.period_end.isoformat(), "basis": rule.basis,
        "rate": str(rule.rate) if rule.rate is not None else None,
        "tiers": [{"threshold": str(t.threshold), "rate": str(t.rate) if t.rate is not None else None,
                   "reward": str(t.reward) if t.reward is not None else None} for t in rule.tiers],
        "approved": rule.approved, "evidence_refs": sorted(rule.evidence_refs),
    }
    normalized_entries = lambda es: [{"source_system": e.source_system, "external_id": e.external_id,
        "supplier_id": e.supplier_id, "date": e.date.isoformat(), "currency": e.currency,
        "amount_net": str(e.amount), "kind": e.kind.value, "posted": e.posted,
        "evidence_refs": sorted(e.evidence_refs), "basis": e.basis,
        "agreement_id": e.agreement_id, "period_start": e.period_start.isoformat() if e.period_start else None,
        "period_end": e.period_end.isoformat() if e.period_end else None} for e in es]
    snapshot = {"rule": normalized_rule, "transactions": normalized_entries(txns),
                "settlements": normalized_entries(credits), "completeness": {
                    "transactions_complete": confirmed_txns, "settlements_complete": confirmed_credits,
                    "agreements_complete": confirmed_amendments}}
    report = {
        "engine_version": "0.1.0", "rule_id": rule.rule_id, "rule_revision": rule.revision,
        "agreement_id": rule.agreement_id, "supplier_id": rule.supplier_id,
        "period_start": rule.period_start.isoformat(), "period_end": rule.period_end.isoformat(),
        "currency": rule.currency, "status": status.value,
        "legal_claim_confirmed": False,
        "eligible_base_net": str(_money(eligible_base)) if eligible_base >= 0 else None,
        "expected_bonus_net": str(expected) if expected is not None else None,
        "recorded_bonus_net": str(_money(recorded)) if recorded >= 0 else None,
        "difference_net": str(difference) if difference is not None else None,
        "calculated_variance_net": str(difference) if difference is not None else None,
        "included_transactions": included, "matched_settlements": matched,
        "excluded_entries": sorted(excluded, key=lambda e: (e["entry"], e["reason"])),
        "warnings": sorted(warnings), "blocking_reasons": sorted(blocking),
        "input_snapshot_sha256": _digest(snapshot),
        "rule_evidence_refs": sorted(rule.evidence_refs),
        "billable_recovery_net": "0.00", "fee_due_net": "0.00",
    }
    return report
