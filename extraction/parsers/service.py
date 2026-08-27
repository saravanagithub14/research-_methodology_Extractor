import logging
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from papers.models import DocumentBlock, Paper
from .base import PDFParser, ParsedDocument
from .docling_parser import DoclingParser
from .pymupdf_parser import PyMuPDFParser

logger = logging.getLogger(__name__)


def parse_paper(paper: Paper, parsers: list[PDFParser] | None = None) -> ParsedDocument:
    paper.status = Paper.Status.PARSING
    paper.save(update_fields=("status",))
    errors: list[str] = []
    for parser in parsers or [DoclingParser(), PyMuPDFParser()]:
        try:
            parsed = parser.parse(Path(paper.source_file.path))
            _persist_parse(paper, parsed)
            return parsed
        except Exception as error:
            logger.warning("PDF parser failed", extra={"paper_id": str(paper.id), "parser": parser.name, "error": str(error)})
            errors.append(f"{parser.name}: {error.__class__.__name__}")
    paper.status, paper.parsing_metadata = Paper.Status.FAILED, {"errors": errors, "failed_at": timezone.now().isoformat()}
    paper.save(update_fields=("status", "parsing_metadata"))
    raise RuntimeError("All configured PDF parsers failed")


def _persist_parse(paper: Paper, parsed: ParsedDocument) -> None:
    with transaction.atomic():
        DocumentBlock.objects.filter(paper=paper).delete()
        DocumentBlock.objects.bulk_create([DocumentBlock(paper=paper, page_number=b.page_number, block_type=b.block_type, heading=b.heading, text=b.text, order_index=b.order_index, parser_metadata=b.metadata) for b in parsed.blocks])
        paper.page_count, paper.status = parsed.page_count, Paper.Status.PARSED
        paper.parsing_metadata = {"parser": parsed.parser_name, **parsed.metadata, "parsed_at": timezone.now().isoformat()}
        paper.save(update_fields=("page_count", "status", "parsing_metadata"))
