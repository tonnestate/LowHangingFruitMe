"""Local Docling adapter: extract cited document segments, never approve rules.

This is a data-reader, not a legal interpretation or a parser for claims.
It accepts only a local regular PDF file; no URLs or remote model calls.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

MAX_PDF_BYTES = 20 * 1024 * 1024
MAX_PAGES = 50
MAX_SEGMENTS = 10_000
MAX_TOTAL_TEXT = 500_000


def _segments_from_document(document: Any, file_sha256: str) -> list[dict[str, Any]]:
    """Turn Docling's document tree into evidence-bound, review-only segments.

    Extraction can be unit-tested with a DoclingDocument-like object; this
    does not constitute a benchmark of OCR or real PDF conversion quality.
    """
    segments: list[dict[str, Any]] = []
    text_bytes = 0
    for index, (item, _level) in enumerate(document.iterate_items()):
        if index >= MAX_SEGMENTS:
            raise ValueError("PDF contains too many document items")
        label = getattr(item, "label", None)
        kind = str(getattr(label, "value", label or "unknown"))
        if kind == "table":
            try:
                table = item.export_to_dataframe(doc=document)
                text = table.to_csv(index=False)
            except Exception as exc:
                raise ValueError(f"Docling table {index} could not be extracted") from exc
        else:
            text = getattr(item, "text", "")
        if not isinstance(text, str) or not text.strip():
            continue
        text_bytes += len(text)
        if text_bytes > MAX_TOTAL_TEXT:
            raise ValueError("PDF extraction exceeds the maximum text budget")
        pages = sorted({int(p.page_no) for p in (getattr(item, "prov", None) or [])
                        if getattr(p, "page_no", None) is not None})
        if pages and (min(pages) < 1 or max(pages) > MAX_PAGES):
            raise ValueError("invalid Docling page reference")
        self_ref = str(getattr(item, "self_ref", "") or f"index:{index}")
        provenance = f"sha256:{file_sha256}#item={index}"
        if pages:
            provenance += "&pages=" + ",".join(map(str, pages))
        segments.append({
            "segment_id": index,
            "kind": kind,
            "pages": pages,
            "docling_ref": self_ref,
            "evidence_ref": provenance,
            "text": text,
        })
    if not segments:
        raise ValueError("Docling returned no text/table evidence; manual review required")
    return segments


def extract_pdf(path: str | Path) -> dict[str, Any]:
    """Convert a verified local PDF to cited review segments using Docling.

    Security precondition: a trusted upload stage has malware-scanned and
    isolated the document. The parser still needs OS process/resource isolation.
    """
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".pdf":
        raise ValueError("expected a regular local PDF file, not a symlink")
    if not 0 < path.stat().st_size <= MAX_PDF_BYTES:
        raise ValueError("PDF too large or empty")
    with path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ValueError("invalid PDF signature")
        handle.seek(0)
        digest = sha256(handle.read()).hexdigest()
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise RuntimeError("Docling is required: install lowhangingfruitme[docs]") from exc
    converter = DocumentConverter(allowed_formats=[InputFormat.PDF])
    result = converter.convert(
        path, raises_on_error=True,
        max_file_size=MAX_PDF_BYTES, max_num_pages=MAX_PAGES,
    )
    try:
        status = str(getattr(result.status, "value", result.status)).lower()
        if status != "success":
            raise ValueError(f"Docling conversion was not complete: {status}")
        segments = _segments_from_document(result.document, digest)
    finally:
        input_data = getattr(result, "input", None)
        release = getattr(input_data, "release", None)
        if callable(release):
            release()
    return {
        "file_sha256": digest,
        "parser": "docling",
        "source_type": "PDF",
        "state": "NEEDS_HUMAN_REVIEW",
        "automatically_approved_rule": None,
        "segments": segments,
    }
