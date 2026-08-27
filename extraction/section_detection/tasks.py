from celery import shared_task

from extraction.section_detection import detect_sections
from papers.models import Paper


@shared_task
def detect_sections_task(paper_id: str) -> dict[str, object]:
    sections = detect_sections(Paper.objects.get(id=paper_id))
    return {"paper_id": paper_id, "sections": len(sections)}
