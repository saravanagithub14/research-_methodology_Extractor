"""Rule-based first-pass section detection with explicit source boundaries."""
from __future__ import annotations

import re

from django.db import transaction

from papers.models import DocumentBlock, DocumentSection, Paper

SECTION_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("methods", ("methods", "materials and methods", "methodology", "experimental procedures", "experimental methods")),
    ("study_design", ("study design",)),
    ("sample_collection", ("sample collection", "patient recruitment", "animal experiments", "cell culture")),
    ("bioinformatics", ("bioinformatics analysis", "computational methods", "data analysis", "sequencing and analysis")),
    ("statistical_analysis", ("statistical analysis", "statistics")),
    ("data_availability", ("data availability", "data and code availability")),
    ("code_availability", ("code availability",)),
    ("supplementary_methods", ("supplementary methods",)),
)


def _normalized_heading(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^[0-9.\s]+", "", value.lower())).strip(" :.-")


def _section_type(heading: str) -> str | None:
    normalized = _normalized_heading(heading)
    for section_type, names in SECTION_RULES:
        if normalized in names:
            return section_type
    return None


def detect_sections(paper: Paper) -> list[DocumentSection]:
    """Persist only headings supported by stored document blocks; no content inference."""
    blocks = list(paper.blocks.all())
    headings = [(index, block, section_type) for index, block in enumerate(blocks)
                if block.block_type == DocumentBlock.BlockType.HEADING
                if (section_type := _section_type(block.text)) is not None]
    heading_positions = [index for index, _block, _kind in headings]
    found: list[tuple[DocumentBlock, DocumentBlock, str]] = []
    for index, block, section_type in headings:
        next_heading_index = next((position for position in heading_positions if position > index), len(blocks))
        end_block = blocks[next_heading_index - 1] if next_heading_index > index else block
        found.append((block, end_block, section_type))

    with transaction.atomic():
        DocumentSection.objects.filter(paper=paper).delete()
        sections = DocumentSection.objects.bulk_create([
            DocumentSection(paper=paper, section_name=start.text.strip(), normalized_section_type=section_type,
                            start_page=start.page_number, end_page=end.page_number, start_block=start,
                            end_block=end, confidence=1.0)
            for start, end, section_type in found
        ])
    return sections
