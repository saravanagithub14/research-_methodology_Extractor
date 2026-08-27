from celery import shared_task

from extraction.parsers import parse_paper
from papers.models import Paper


@shared_task(bind=True, autoretry_for=(OSError,), retry_backoff=True, max_retries=2)
def parse_paper_task(self, paper_id: str) -> dict[str, object]:
    parsed = parse_paper(Paper.objects.get(id=paper_id))
    return {"paper_id": paper_id, "parser": parsed.parser_name, "blocks": len(parsed.blocks)}
