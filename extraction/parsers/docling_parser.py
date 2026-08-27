from pathlib import Path

from .base import ParsedBlock, ParsedDocument


class DoclingParser:
    """Primary parser; the service falls back when Docling cannot convert a PDF."""
    name = "docling"

    def parse(self, source_path: Path) -> ParsedDocument:
        from docling.document_converter import DocumentConverter

        document = DocumentConverter().convert(str(source_path)).document
        blocks, order_index = [], 0
        for item, _level in document.iterate_items():
            text = getattr(item, "text", None)
            if not isinstance(text, str) or not text.strip():
                continue
            provenance = getattr(item, "prov", []) or []
            page_number = getattr(provenance[0], "page_no", 1) if provenance else 1
            label = str(getattr(item, "label", "unknown")).lower()
            block_type = "heading" if "title" in label or "section" in label else "paragraph"
            blocks.append(ParsedBlock(page_number, block_type, text.strip(), order_index))
            order_index += 1
        if not blocks:
            raise ValueError("Docling returned no text blocks")
        return ParsedDocument(max(block.page_number for block in blocks), blocks, self.name)
