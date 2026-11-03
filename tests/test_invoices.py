"""Preview-only UBL and CII XML evidence regression, using synthetic invoices."""
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from lowhangingfruitme.invoices import extract_invoice_preview

UBL=b'''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
 <cbc:ID>INVOICE-SYN-100</cbc:ID>
 <cbc:IssueDate>2025-05-10</cbc:IssueDate>
 <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
 <cac:AccountingSupplierParty><cac:Party><cac:PartyLegalEntity>
 <cbc:RegistrationName>Synthetic Supplier</cbc:RegistrationName>
 </cac:PartyLegalEntity></cac:Party></cac:AccountingSupplierParty>
 <cac:LegalMonetaryTotal><cbc:TaxExclusiveAmount currencyID="EUR">120.00</cbc:TaxExclusiveAmount></cac:LegalMonetaryTotal>
 <cac:InvoiceLine><cbc:ID>1</cbc:ID><cbc:InvoicedQuantity>2</cbc:InvoicedQuantity>
 <cbc:LineExtensionAmount currencyID="EUR">120.00</cbc:LineExtensionAmount>
 <cac:Item><cbc:Name>Spare part</cbc:Name><cac:SellersItemIdentification><cbc:ID>SKU-SYN</cbc:ID>
 </cac:SellersItemIdentification></cac:Item>
 <cac:Price><cbc:PriceAmount currencyID="EUR">60.00</cbc:PriceAmount></cac:Price>
 </cac:InvoiceLine>
</Invoice>'''

CII=b'''<?xml version="1.0"?>
<rsm:CrossIndustryInvoice
 xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
 xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
 xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
<rsm:ExchangedDocument><ram:ID>CII-SYN-123</ram:ID>
<ram:IssueDateTime><udt:DateTimeString format="102">20250511</udt:DateTimeString></ram:IssueDateTime></rsm:ExchangedDocument>
<rsm:SupplyChainTradeTransaction>
<ram:IncludedSupplyChainTradeLineItem>
<ram:AssociatedDocumentLineDocument><ram:LineID>1</ram:LineID></ram:AssociatedDocumentLineDocument>
<ram:SpecifiedTradeProduct><ram:Name>Test material</ram:Name>
<ram:SellerAssignedID>TEST-SKU</ram:SellerAssignedID></ram:SpecifiedTradeProduct>
<ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice>
<ram:ChargeAmount>25.00</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement>
<ram:SpecifiedLineTradeDelivery><ram:BilledQuantity>4</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>
<ram:SpecifiedLineTradeSettlement><ram:SpecifiedTradeSettlementLineMonetarySummation>
<ram:LineTotalAmount>100.00</ram:LineTotalAmount>
</ram:SpecifiedTradeSettlementLineMonetarySummation></ram:SpecifiedLineTradeSettlement>
</ram:IncludedSupplyChainTradeLineItem>
<ram:ApplicableHeaderTradeAgreement><ram:SellerTradeParty><ram:Name>Sample seller</ram:Name>
</ram:SellerTradeParty></ram:ApplicableHeaderTradeAgreement>
<ram:ApplicableHeaderTradeSettlement><ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
<ram:SpecifiedTradeSettlementHeaderMonetarySummation>
<ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount>
</ram:SpecifiedTradeSettlementHeaderMonetarySummation></ram:ApplicableHeaderTradeSettlement>
</rsm:SupplyChainTradeTransaction></rsm:CrossIndustryInvoice>'''


class XMLInvoiceTests(unittest.TestCase):
    def setUp(self):
        t=TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.home=Path(t.name)
    def write(self,data):
        f=self.home/"synthetic.xml"
        f.write_bytes(data)
        return f

    def test_ubl_invoice_lines_and_source_provenance(self):
        result=extract_invoice_preview(self.write(UBL))
        self.assertEqual(result["standard_family"],"UBL")
        self.assertEqual(result["document_kind"],"INVOICE")
        self.assertEqual(result["document_id"],"INVOICE-SYN-100")
        self.assertEqual(result["issue_date"],"2025-05-10")
        self.assertEqual(result["currency"],"EUR")
        self.assertEqual(result["supplier_name"],"Synthetic Supplier")
        self.assertEqual(result["document_net_amount"],"120.00")
        self.assertEqual(result["lines"][0]["seller_sku"],"SKU-SYN")
        self.assertEqual(result["lines"][0]["quantity"],"2")
        self.assertEqual(result["lines"][0]["net_amount"],"120.00")
        self.assertIn(sha256(UBL).hexdigest(),result["lines"][0]["source_ref"])
        self.assertFalse(result["accounting_posted"])
        self.assertFalse(result["schema_validated"])
        self.assertFalse(result["usable_for_audit"])

    def test_cii_header_and_item_preview(self):
        result=extract_invoice_preview(self.write(CII))
        self.assertEqual(result["standard_family"],"CII")
        self.assertEqual(result["document_id"],"CII-SYN-123")
        self.assertEqual(result["issue_date"],"2025-05-11")
        self.assertEqual(result["document_net_amount"],"100.00")
        self.assertEqual(result["lines"][0]["net_amount"],"100.00")
        self.assertEqual(result["lines"][0]["unit_price"],"25.00")
        self.assertEqual(result["supplier_name"],"Sample seller")
        self.assertTrue(result["review_required"])

    def test_ubl_credit_note_never_automatically_posted(self):
        data=UBL.replace(b'<Invoice xmlns=',b'<CreditNote xmlns=').replace(
            b'schema:xsd:Invoice-2',b'schema:xsd:CreditNote-2').replace(
            b'</Invoice>',b'</CreditNote>').replace(
            b'<cac:InvoiceLine>',b'<cac:CreditNoteLine>').replace(
            b'</cac:InvoiceLine>',b'</cac:CreditNoteLine>').replace(
            b'<cbc:InvoicedQuantity>',b'<cbc:CreditedQuantity>').replace(
            b'</cbc:InvoicedQuantity>',b'</cbc:CreditedQuantity>')
        result=extract_invoice_preview(self.write(data))
        self.assertEqual(result["document_kind"],"CREDIT_NOTE")
        self.assertFalse(result["accounting_posted"])

    def test_unsafe_entities_and_unrecognized_namespace_rejected(self):
        attack=(b'<!DOCTYPE Invoice [<!ENTITY ext SYSTEM "file:///etc/passwd">]>'
                b'<Invoice>&ext;</Invoice>')
        with self.assertRaises(ValueError):
            extract_invoice_preview(self.write(attack))
        with self.assertRaisesRegex(ValueError,"unsupported invoice"):
            extract_invoice_preview(self.write(b"<Invoice><ID>1</ID></Invoice>"))

    def test_currency_and_money_values_are_strict(self):
        with self.assertRaisesRegex(ValueError,"invalid decimal"):
            extract_invoice_preview(self.write(UBL.replace(b">120.00</cbc:LineExtensionAmount>",
                b">NaN</cbc:LineExtensionAmount>")))
        with self.assertRaisesRegex(ValueError,"valid currency"):
            extract_invoice_preview(self.write(UBL.replace(b">EUR</cbc:DocumentCurrencyCode>",
                b">NOT_EUR</cbc:DocumentCurrencyCode>")))

if __name__=="__main__":
    unittest.main()
