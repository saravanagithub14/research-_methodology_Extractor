from __future__ import annotations

import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models


def paper_upload_path(instance: "Paper", filename: str) -> str:
    return f"papers/{instance.id}/{Path(filename).name}"


class Paper(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PARSING = "parsing", "Parsing"
        FAILED = "failed", "Failed"
        PARSED = "parsed", "Parsed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_file = models.FileField(upload_to=paper_upload_path)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.UPLOADED)
    parsing_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.original_filename

    def clean(self) -> None:
        super().clean()
        if self.source_file and not self.source_file.name.lower().endswith(".pdf"):
            raise ValidationError({"source_file": "Only PDF files are accepted."})


class DocumentBlock(models.Model):
    class BlockType(models.TextChoices):
        HEADING = "heading", "Heading"
        PARAGRAPH = "paragraph", "Paragraph"
        TABLE = "table", "Table"
        CAPTION = "caption", "Caption"
        LIST = "list", "List"
        REFERENCE = "reference", "Reference"
        UNKNOWN = "unknown", "Unknown"

    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="blocks")
    page_number = models.PositiveIntegerField()
    block_type = models.CharField(max_length=16, choices=BlockType.choices, default=BlockType.UNKNOWN)
    heading = models.CharField(max_length=500, blank=True)
    text = models.TextField()
    order_index = models.PositiveIntegerField()
    parser_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("order_index",)
        constraints = [models.UniqueConstraint(fields=("paper", "order_index"), name="unique_paper_block_order")]


class DocumentSection(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="sections")
    section_name = models.CharField(max_length=500)
    normalized_section_type = models.CharField(max_length=64)
    start_page = models.PositiveIntegerField()
    end_page = models.PositiveIntegerField()
    start_block = models.ForeignKey(DocumentBlock, on_delete=models.CASCADE, related_name="sections_starting")
    end_block = models.ForeignKey(DocumentBlock, on_delete=models.CASCADE, related_name="sections_ending")
    confidence = models.FloatField()

    class Meta:
        ordering = ("start_block__order_index",)
        constraints = [models.UniqueConstraint(fields=("paper", "start_block"), name="unique_paper_section_start")]
