from pathlib import Path

import fitz

from .base import ParsedBlock, ParsedDocument


class PyMuPDFParser:
    name = "pymupdf"

    def parse(self, source_path: Path) -> ParsedDocument:
        blocks, order_index = [], 0
        with fitz.open(source_path) as document:
            for page_number, page in enumerate(document, start=1):
                for raw in page.get_text("blocks", sort=True):
                    text = raw[4].strip()
                    if text:
                        blocks.append(ParsedBlock(page_number, self._classify(text), text, order_index, metadata={"bbox": [round(v, 2) for v in raw[:4]]}))
                        order_index += 1
            return ParsedDocument(len(document), blocks, self.name)

    @staticmethod
    def _classify(text: str) -> str:
        value = text.strip()
        if value.lower().startswith("table "):
            return "table"
        if value.lower().startswith(("figure ", "fig. ")):
            return "caption"
        if len(value) < 140 and "\n" not in value and not value.endswith((".", ";", ":")):
            return "heading"
        if value.startswith(("•", "- ", "1. ")):
            return "list"
        return "paragraph"
