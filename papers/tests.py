from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.core.management import call_command

from .forms import PaperUploadForm
from .models import DocumentBlock, Paper
from extraction.parsers.pymupdf_parser import PyMuPDFParser
from extraction.parsers.service import parse_paper
from extraction.section_detection import detect_sections
from extraction.models import ExtractionRun, MethodStep
from extraction.workflow import build_workflow, mermaid_diagram
from extraction.models import ExtractedEntity
from extraction.reproducibility import assess_reproducibility


class PaperUploadTests(TestCase):
    def test_dashboard_is_available(self):
        self.assertEqual(self.client.get(reverse("papers:dashboard")).status_code, 200)

    def test_sections_api_is_available(self):
        paper = Paper.objects.create(original_filename="api.pdf", source_file=SimpleUploadedFile("api.pdf", b"%PDF-1.4"))
        response = self.client.get(f"/api/papers/{paper.id}/sections/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_section_evidence_page_shows_source_block(self):
        paper = Paper.objects.create(original_filename="evidence.pdf", source_file=SimpleUploadedFile("evidence.pdf", b"%PDF-1.4"))
        start = DocumentBlock.objects.create(paper=paper, page_number=1, block_type="heading", text="Methods", order_index=0)
        block = DocumentBlock.objects.create(paper=paper, page_number=1, block_type="paragraph", text="RNA was extracted using TRIzol.", order_index=1)
        from .models import DocumentSection
        section = DocumentSection.objects.create(paper=paper, section_name="Methods", normalized_section_type="methods", start_page=1, end_page=1, start_block=start, end_block=block, confidence=1)
        response = self.client.get(reverse("papers:section-evidence", args=[paper.id, section.id]))
        self.assertContains(response, "RNA was extracted using TRIzol.")

    def test_extract_action_requires_parsed_paper(self):
        paper = Paper.objects.create(original_filename="unparsed.pdf", source_file=SimpleUploadedFile("unparsed.pdf", b"%PDF-1.4"))
        response = self.client.post(reverse("papers:extract", args=[paper.id]), follow=True)
        self.assertContains(response, "Parse the PDF before requesting methodology extraction.")

    def test_superuser_initialization_is_skipped_without_environment(self):
        from io import StringIO
        output = StringIO()
        call_command("ensure_superuser", stdout=output)
        self.assertIn("skipping", output.getvalue().lower())

    def test_pdf_upload_is_persisted(self):
        response = self.client.post(reverse("papers:upload"), {"source_file": SimpleUploadedFile("study.pdf", b"%PDF-1.4 test")})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Paper.objects.count(), 1)

    def test_non_pdf_is_rejected(self):
        form = PaperUploadForm(files={"source_file": SimpleUploadedFile("notes.txt", b"not pdf")})
        self.assertFalse(form.is_valid())

    def test_parser_persists_page_addressable_blocks(self):
        import fitz
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile(suffix=".pdf") as temporary_file:
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "Methods")
            page.insert_text((72, 108), "Total RNA was extracted using TRIzol.")
            document.save(temporary_file.name)
            document.close()
            with open(temporary_file.name, "rb") as handle:
                paper = Paper.objects.create(original_filename="methods.pdf", source_file=SimpleUploadedFile("methods.pdf", handle.read()))

        parsed = parse_paper(paper, parsers=[PyMuPDFParser()])
        paper.refresh_from_db()
        self.assertEqual(parsed.parser_name, "pymupdf")
        self.assertEqual(paper.status, Paper.Status.PARSED)
        self.assertEqual(paper.page_count, 1)
        self.assertGreaterEqual(paper.blocks.count(), 1)
        self.assertEqual(paper.blocks.first().page_number, 1)

    def test_section_detector_keeps_source_boundaries(self):
        paper = Paper.objects.create(original_filename="study.pdf", source_file=SimpleUploadedFile("study.pdf", b"%PDF-1.4"))
        blocks = DocumentBlock.objects.bulk_create([
            DocumentBlock(paper=paper, page_number=1, block_type="heading", text="Materials and Methods", order_index=0),
            DocumentBlock(paper=paper, page_number=1, block_type="paragraph", text="Samples were collected.", order_index=1),
            DocumentBlock(paper=paper, page_number=2, block_type="heading", text="Statistical Analysis", order_index=2),
            DocumentBlock(paper=paper, page_number=2, block_type="paragraph", text="Tests were two-sided.", order_index=3),
            DocumentBlock(paper=paper, page_number=3, block_type="heading", text="Results", order_index=4),
        ])
        detected = detect_sections(paper)
        self.assertEqual(len(detected), 2)
        methods = paper.sections.get(normalized_section_type="methods")
        self.assertEqual(methods.start_block_id, blocks[0].id)
        self.assertEqual(methods.end_block_id, blocks[1].id)
        self.assertEqual(methods.start_page, 1)

    def test_parse_action_processes_uploaded_pdf(self):
        import fitz
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(suffix=".pdf") as temporary_file:
            document = fitz.open()
            document.new_page().insert_text((72, 72), "Methods")
            document.save(temporary_file.name)
            document.close()
            with open(temporary_file.name, "rb") as handle:
                paper = Paper.objects.create(original_filename="parse.pdf", source_file=SimpleUploadedFile("parse.pdf", handle.read()))
        response = self.client.post(reverse("papers:parse", args=[paper.id]))
        paper.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(paper.status, Paper.Status.PARSED)

    def test_workflow_marks_missing_dependencies_as_inferred(self):
        paper = Paper.objects.create(original_filename="workflow.pdf", source_file=SimpleUploadedFile("workflow.pdf", b"%PDF-1.4"))
        run = ExtractionRun.objects.create(paper=paper, model="gpt-4o-mini")
        MethodStep.objects.create(extraction_run=run, external_id="step_1", order=1, category="RNA Extraction", action="Extract RNA", description="", confidence=1)
        MethodStep.objects.create(extraction_run=run, external_id="step_2", order=2, category="Sequencing", action="Sequence", description="", confidence=1)
        edges = build_workflow(run)
        self.assertEqual(len(edges), 1)
        self.assertTrue(edges[0].is_inferred)
        self.assertIn("inferred", mermaid_diagram(run))

    def test_reproducibility_score_measures_reporting_completeness(self):
        paper = Paper.objects.create(original_filename="rna.pdf", source_file=SimpleUploadedFile("rna.pdf", b"%PDF-1.4"))
        run = ExtractionRun.objects.create(paper=paper, model="gpt-4o-mini")
        ExtractedEntity.objects.create(run=run, entity_type="software", original_name="STAR", status="reported")
        ExtractedEntity.objects.create(run=run, entity_type="instrument", original_name="Illumina NovaSeq", status="reported")
        assessment = assess_reproducibility(run)
        self.assertIn("Alignment software", assessment.reported)
        self.assertIn("Sequencing platform", assessment.reported)
        self.assertIn("Data accession", assessment.missing)
        self.assertEqual(assessment.score, 18)
