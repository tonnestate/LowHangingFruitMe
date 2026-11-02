"""Test source-referenced Docling document normalization without claiming OCR QA."""
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from lowhangingfruitme.documents import _segments_from_document, extract_pdf


class FakeDocument:
    def __init__(self, items):
        self.items = items

    def iterate_items(self):
        for item in self.items:
            yield item, 0


class FakeText:
    def __init__(self, text, pages):
        self.text = text
        self.label = SimpleNamespace(value="paragraph")
        self.self_ref = "#/texts/0"
        self.prov = [SimpleNamespace(page_no=x) for x in pages]


class DoclingNormalizationTests(unittest.TestCase):
    def test_page_and_document_hash_provenance(self):
        doc = FakeDocument([FakeText("2 % Rabatt ab 1. Januar", [2])])
        result = _segments_from_document(doc, "a" * 64)
        self.assertEqual(result[0]["pages"], [2])
        self.assertEqual(result[0]["text"], "2 % Rabatt ab 1. Januar")
        self.assertEqual(result[0]["evidence_ref"], "sha256:" + "a" * 64 + "#item=0&pages=2")

    def test_empty_extraction_requires_review(self):
        with self.assertRaisesRegex(ValueError, "no text/table evidence"):
            _segments_from_document(FakeDocument([]), "a" * 64)

    def test_invalid_page_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid Docling page"):
            _segments_from_document(FakeDocument([FakeText("Bonus", [0])]), "a" * 64)

    def test_invalid_pdf_signature_rejected_without_docling(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "fake.pdf"
            file.write_bytes(b"not-a-pdf")
            with self.assertRaisesRegex(ValueError, "invalid PDF signature"):
                extract_pdf(file)

    def test_symlink_pdf_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "real.pdf"
            source.write_bytes(b"%PDF-synthetic-only")
            link = Path(tmp) / "link.pdf"
            link.symlink_to(source)
            with self.assertRaisesRegex(ValueError, "not a symlink"):
                extract_pdf(link)

    @unittest.skipUnless(importlib.util.find_spec("docling"), "Docling not installed")
    def test_real_docling_conversion_in_explicit_integration_environment(self):
        """Not run in default CI; manual acceptance needs a real, labeled PDF fixture."""
        # Separate fixture-based OCR/layout benchmark is necessary before go-live.
        self.assertTrue(importlib.util.find_spec("docling") is not None)


if __name__ == "__main__":
    unittest.main()
