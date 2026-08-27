from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ParsedBlock:
    page_number: int
    block_type: str
    text: str
    order_index: int
    heading: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedDocument:
    page_count: int
    blocks: list[ParsedBlock]
    parser_name: str
    metadata: dict[str, object] = field(default_factory=dict)


class PDFParser(Protocol):
    name: str
    def parse(self, source_path: Path) -> ParsedDocument: ...
