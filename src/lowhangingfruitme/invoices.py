"""Secure preview-only UBL/XRechnung and CII/ZUGFeRD XML extraction.

Never promotes invoice contents into a posted ERP ledger or an approved
contract rule. No implicit supplier identity, FX, tax or completeness.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
import re
from typing import Any

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

UBL_INVOICE="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
UBL_CREDIT="urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"
CBC="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
CAC="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
CII="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
RAM="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
RSM=CII
UDT="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100"
MAX_XML=16*1024*1024
MAX_ELEMENTS=150000
MAX_LINES=10000
NUMBER=re.compile(r"^-?(?:0|[1-9]\d{0,13})(?:\.\d{1,8})?$")
CURRENCY=re.compile(r"^[A-Z]{3}$")


def _tag(namespace: str, local: str) -> str:
    return "{"+namespace+"}"+local


def _text(element: Any, *path: str) -> str | None:
    current=element
    for name in path:
        if current is None:
            return None
        current=current.find(name)
    if current is None or current.text is None:
        return None
    return current.text.strip() or None


def _amount(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    if not NUMBER.fullmatch(value):
        raise ValueError("invalid decimal content in "+field)
    try:
        amount=Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid decimal in "+field) from exc
    if not amount.is_finite():
        raise ValueError("non-finite monetary content")
    return format(amount,"f")


def _date(raw: str | None, kind: str, fmt: str | None = None) -> str | None:
    if raw is None:
        return None
    if kind=="CII" and fmt=="102":
        if not re.fullmatch(r"\d{8}",raw):
            raise ValueError("invalid CII format 102 date")
        raw=raw[:4]+"-"+raw[4:6]+"-"+raw[6:8]
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError as exc:
        raise ValueError("unsupported invoice date format") from exc


def _ubl(root: Any, digest: str, credit: bool) -> dict[str, Any]:
    line_name="CreditNoteLine" if credit else "InvoiceLine"
    quantity_name="CreditedQuantity" if credit else "InvoicedQuantity"
    lines=root.findall(_tag(CAC,line_name))
    if len(lines)>MAX_LINES:
        raise ValueError("invoice exceeds line count limit")
    entries=[]
    for no,item in enumerate(lines,start=1):
        row={
            "line_id":_text(item,_tag(CBC,"ID")),
            "description":_text(item,_tag(CAC,"Item"),_tag(CBC,"Name")),
            "seller_sku":_text(item,_tag(CAC,"Item"),_tag(CAC,"SellersItemIdentification"),_tag(CBC,"ID")),
            "quantity":_amount(_text(item,_tag(CBC,quantity_name)),"quantity"),
            "net_amount":_amount(_text(item,_tag(CBC,"LineExtensionAmount")),"line amount"),
            "unit_price":_amount(_text(item,_tag(CAC,"Price"),_tag(CBC,"PriceAmount")),"unit price"),
            "source_ref":"sha256:"+digest+"#"+line_name+"["+str(no)+"]",
        }
        entries.append(row)
    return {
        "standard_family":"UBL",
        "document_kind":"CREDIT_NOTE" if credit else "INVOICE",
        "document_id":_text(root,_tag(CBC,"ID")),
        "issue_date":_date(_text(root,_tag(CBC,"IssueDate")),"UBL"),
        "currency":_text(root,_tag(CBC,"DocumentCurrencyCode")),
        "supplier_name":(
            _text(root,_tag(CAC,"AccountingSupplierParty"),_tag(CAC,"Party"),
                  _tag(CAC,"PartyLegalEntity"),_tag(CBC,"RegistrationName"))
            or _text(root,_tag(CAC,"AccountingSupplierParty"),_tag(CAC,"Party"),
                     _tag(CAC,"PartyName"),_tag(CBC,"Name"))
        ),
        "document_net_amount":_amount(
            _text(root,_tag(CAC,"LegalMonetaryTotal"),_tag(CBC,"TaxExclusiveAmount")),
            "document net amount",
        ),
        "line_count":len(entries),"lines":entries,
    }


def _cii(root: Any, digest: str) -> dict[str, Any]:
    transaction=root.find(_tag(RSM,"SupplyChainTradeTransaction"))
    if transaction is None:
        raise ValueError("CII trade transaction missing")
    line_tags=transaction.findall(_tag(RAM,"IncludedSupplyChainTradeLineItem"))
    if len(line_tags)>MAX_LINES:
        raise ValueError("invoice exceeds line count limit")
    header=transaction.find(_tag(RAM,"ApplicableHeaderTradeSettlement"))
    date_element=root.find(_tag(RSM,"ExchangedDocument"))
    date_entry=(_text(date_element,_tag(RAM,"IssueDateTime"),
                      _tag(UDT,"DateTimeString")) if date_element is not None else None)
    date_meta=(date_element.find("./"+_tag(RAM,"IssueDateTime")+"/"+
                                  _tag(UDT,"DateTimeString")) if date_element is not None else None)
    fmt=date_meta.attrib.get("format") if date_meta is not None else None
    trade=transaction.find(_tag(RAM,"ApplicableHeaderTradeAgreement"))
    supplier=_text(trade,_tag(RAM,"SellerTradeParty"),_tag(RAM,"Name")) if trade is not None else None
    entries=[]
    for no,item in enumerate(line_tags,start=1):
        row={
            "line_id":_text(item,_tag(RAM,"AssociatedDocumentLineDocument"),_tag(RAM,"LineID")),
            "description":_text(item,_tag(RAM,"SpecifiedTradeProduct"),_tag(RAM,"Name")),
            "seller_sku":_text(item,_tag(RAM,"SpecifiedTradeProduct"),_tag(RAM,"SellerAssignedID")),
            "quantity":_amount(
                _text(item,_tag(RAM,"SpecifiedLineTradeDelivery"),_tag(RAM,"BilledQuantity")),"quantity"),
            "net_amount":_amount(
                _text(item,_tag(RAM,"SpecifiedLineTradeSettlement"),
                      _tag(RAM,"SpecifiedTradeSettlementLineMonetarySummation"),
                      _tag(RAM,"LineTotalAmount")),"line amount"),
            "unit_price":_amount(
                _text(item,_tag(RAM,"SpecifiedLineTradeAgreement"),
                      _tag(RAM,"NetPriceProductTradePrice"),_tag(RAM,"ChargeAmount")),"unit price"),
            "source_ref":"sha256:"+digest+"#IncludedSupplyChainTradeLineItem["+str(no)+"]",
        }
        entries.append(row)
    return {
        "standard_family":"CII",
        "document_kind":"INVOICE_OR_CORRECTION_REQUIRES_REVIEW",
        "document_id":_text(date_element,_tag(RAM,"ID")) if date_element is not None else None,
        "issue_date":_date(date_entry,"CII",fmt),
        "currency":_text(header,_tag(RAM,"InvoiceCurrencyCode")) if header is not None else None,
        "supplier_name":supplier,
        "document_net_amount":(
            _amount(_text(header,_tag(RAM,"SpecifiedTradeSettlementHeaderMonetarySummation"),
                          _tag(RAM,"TaxBasisTotalAmount")),"tax basis")
            if header is not None else None),
        "line_count":len(entries),"lines":entries,
    }


def extract_invoice_preview(path: str | Path) -> dict[str, Any]:
    """Parse untrusted XML from a previously scanned, immutable private copy.

    This only extracts candidates, never asserts a valid XRechnung profile,
    creates a posted booking, or replaces ERP reconciliation.
    """
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.suffix.lower()!=".xml":
        raise ValueError("invoice preview requires a regular XML source")
    data=path.read_bytes()
    if not 0<len(data)<=MAX_XML or b"\0" in data:
        raise ValueError("invoice XML violates size or content bounds")
    digest=sha256(data).hexdigest()
    try:
        root=ET.fromstring(data)
    except (ET.ParseError, DefusedXmlException) as exc:
        raise ValueError("invalid XML document") from exc
    if sum(1 for _ in root.iter())>MAX_ELEMENTS:
        raise ValueError("invoice XML exceeds element budget")
    if root.tag==_tag(UBL_INVOICE,"Invoice"):
        parsed=_ubl(root,digest,False)
    elif root.tag==_tag(UBL_CREDIT,"CreditNote"):
        parsed=_ubl(root,digest,True)
    elif root.tag==_tag(CII,"CrossIndustryInvoice"):
        parsed=_cii(root,digest)
    else:
        raise ValueError("unsupported invoice namespace and root")
    if not parsed["document_id"] or not parsed["currency"] or not CURRENCY.fullmatch(parsed["currency"]):
        raise ValueError("invoice missing document ID or valid currency")
    return {
        **parsed,
        "source_sha256":digest,
        "source_reference":"sha256:"+digest+"#document",
        "review_required":True,
        "accounting_posted":False,
        "schema_validated":False,
        "erp_completeness_proven":False,
        "usable_for_audit":False,
    }
