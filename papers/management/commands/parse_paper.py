from django.core.management.base import BaseCommand, CommandError

from extraction.parsers import parse_paper
from papers.models import Paper


class Command(BaseCommand):
    help = "Parse one uploaded PDF and persist source-derived document blocks."

    def add_arguments(self, parser):
        parser.add_argument("paper_id")

    def handle(self, *args, **options):
        try:
            paper = Paper.objects.get(id=options["paper_id"])
        except Paper.DoesNotExist as error:
            raise CommandError("Paper not found") from error
        parsed = parse_paper(paper)
        self.stdout.write(self.style.SUCCESS(f"Parsed {len(parsed.blocks)} blocks with {parsed.parser_name}."))
