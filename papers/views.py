from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from .forms import PaperUploadForm
from .models import DocumentSection, Paper


def dashboard(request):
    return render(request, "papers/dashboard.html", {"papers": Paper.objects.all()[:20]})


def upload_paper(request):
    form = PaperUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        paper = form.save(commit=False)
        paper.original_filename = paper.source_file.name
        paper.save()
        return redirect("papers:detail", paper_id=paper.id)
    return render(request, "papers/upload.html", {"form": form})


def paper_detail(request, paper_id):
    return render(request, "papers/detail.html", {"paper": get_object_or_404(Paper, id=paper_id)})


def paper_sections(request, paper_id):
    return render(request, "papers/sections.html", {"paper": get_object_or_404(Paper, id=paper_id)})


def section_evidence(request, paper_id, section_id):
    paper = get_object_or_404(Paper, id=paper_id)
    section = get_object_or_404(DocumentSection, id=section_id, paper=paper)
    blocks = paper.blocks.filter(order_index__gte=section.start_block.order_index, order_index__lte=section.end_block.order_index)
    return render(request, "papers/evidence.html", {"paper": paper, "section": section, "blocks": blocks})


def parse_paper_view(request, paper_id):
    if request.method != "POST":
        return redirect("papers:detail", paper_id=paper_id)
    paper = get_object_or_404(Paper, id=paper_id)
    try:
        from extraction.parsers import parse_paper
        from extraction.section_detection import detect_sections

        parse_paper(paper)
        detect_sections(paper)
    except Exception:
        messages.error(request, "Parsing failed. The paper was not modified beyond its recorded parsing status.")
        return redirect("papers:detail", paper_id=paper.id)
    messages.success(request, "PDF parsed successfully. Source blocks and detected sections are available.")
    return redirect("papers:sections", paper_id=paper.id)


def extract_paper_view(request, paper_id):
    if request.method != "POST":
        return redirect("papers:detail", paper_id=paper_id)
    paper = get_object_or_404(Paper, id=paper_id)
    if not paper.blocks.exists():
        messages.error(request, "Parse the PDF before requesting methodology extraction.")
        return redirect("papers:detail", paper_id=paper.id)
    try:
        from extraction.services import run_entity_extraction
        from extraction.reproducibility import assess_reproducibility
        run = run_entity_extraction(paper)
        assess_reproducibility(run)
    except Exception as error:
        messages.error(request, f"Methodology extraction was not completed: {str(error)[:240]}")
        return redirect("papers:detail", paper_id=paper.id)
    return redirect("papers:results", paper_id=paper.id)


def paper_results(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    run = paper.extraction_runs.filter(status="completed").order_by("-id").first()
    labels = {"reagent": "Reagents", "instrument": "Instruments", "software": "Software", "dataset": "Datasets", "statistical_method": "Statistical / Analytical Methods"}
    groups = []
    if run:
        for entity_type, label in labels.items():
            cards = []
            for entity in run.entities.filter(entity_type=entity_type).prefetch_related("evidence"):
                name_key = entity.original_name.strip().lower()
                if name_key in {"", "unnamed dataset", "random", "p-value"}:
                    continue
                evidence_text = " ".join(item.quote for item in entity.evidence.all()).lower()
                if "downloaded from" in evidence_text or (entity_type == "statistical_method" and "(2001)" in evidence_text):
                    continue
                fields = [{"label": key.replace("_", " ").title(), "value": value} for key, value in entity.attributes.items() if value not in (None, "", {}, [])]
                if entity_type == "software" and not any(field["label"] == "Version" for field in fields):
                    fields.append({"label": "Version", "value": "Not reported"})
                cards.append({"name": entity.original_name, "fields": fields, "evidence": entity.evidence.all()})
            if cards:
                groups.append({"label": label, "cards": cards})
    steps = [] if not run else list(run.method_steps.all())
    pipeline = " → ".join(step.action for step in steps)
    return render(request, "papers/results.html", {"paper": paper, "run": run, "groups": groups, "steps": steps, "pipeline": pipeline})
