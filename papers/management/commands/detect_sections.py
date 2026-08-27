from django.core.management.base import BaseCommand, CommandError

from extraction.section_detection import detect_sections
from papers.models import Paper


class Command(BaseCommand):
    help = "Detect and persist recognized scientific sections for one parsed paper."

    def add_arguments(self, parser):
        parser.add_argument("paper_id")

    def handle(self, *args, **options):
        try:
            paper = Paper.objects.get(id=options["paper_id"])
        except Paper.DoesNotExist as error:
            raise CommandError("Paper not found") from error
        sections = detect_sections(paper)
        self.stdout.write(self.style.SUCCESS(f"Detected {len(sections)} sections."))
