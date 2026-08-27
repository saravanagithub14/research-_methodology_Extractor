from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Paper
from .serializers import PaperSerializer
from extraction.models import ExtractionRun
from extraction.workflow import mermaid_diagram


class PaperListCreateView(generics.ListCreateAPIView):
    queryset = Paper.objects.all()
    serializer_class = PaperSerializer


class PaperDetailView(generics.RetrieveAPIView):
    queryset = Paper.objects.all()
    serializer_class = PaperSerializer


def _run(paper: Paper):
    return paper.extraction_runs.filter(status="completed").order_by("-id").first()


@api_view(["GET"])
def paper_sections(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    return Response([{"name": s.section_name, "type": s.normalized_section_type, "start_page": s.start_page, "end_page": s.end_page, "confidence": s.confidence} for s in paper.sections.all()])


@api_view(["GET"])
def paper_methods(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    run = _run(paper)
    return Response([] if not run else [{"id": s.external_id, "order": s.order, "category": s.category, "action": s.action, "description": s.description, "inputs": s.inputs, "outputs": s.outputs, "parameters": s.parameters, "confidence": s.confidence} for s in run.method_steps.all()])


@api_view(["GET"])
def paper_workflow(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    run = _run(paper)
    if not run:
        return Response({"nodes": [], "edges": [], "mermaid": "flowchart TD"})
    return Response({"nodes": [{"id": s.external_id, "label": s.action, "category": s.category} for s in run.method_steps.all()], "edges": [{"source": e.source_step.external_id, "target": e.target_step.external_id, "inferred": e.is_inferred, "confidence": e.confidence} for e in run.workflow_edges.select_related("source_step", "target_step")], "mermaid": mermaid_diagram(run)})


@api_view(["GET"])
def paper_reproducibility(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    run = _run(paper)
    assessment = getattr(run, "reproducibility_assessment", None) if run else None
    return Response(None if not assessment else {"score": assessment.score, "reported": assessment.reported, "missing": assessment.missing, "ambiguous": assessment.ambiguous, "recommendations": assessment.recommendations})


@api_view(["GET"])
def paper_export(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    run = _run(paper)
    return Response({"paper": PaperSerializer(paper).data, "sections": [{"name": s.section_name, "type": s.normalized_section_type, "start_page": s.start_page, "end_page": s.end_page} for s in paper.sections.all()], "extraction_run": None if not run else {"id": run.id, "model": run.model, "status": run.status}, "methods": [] if not run else [{"id": s.external_id, "order": s.order, "action": s.action, "evidence": [{"page": e.page_number, "quote": e.quote} for e in s.evidence.all()]} for s in run.method_steps.all()]})
