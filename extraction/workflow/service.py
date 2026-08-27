"""Workflow graph construction from explicit procedure-step dependencies."""
from __future__ import annotations

from django.db import transaction

from extraction.models import ExtractionRun, WorkflowEdge


def build_workflow(run: ExtractionRun) -> list[WorkflowEdge]:
    steps = {step.external_id: step for step in run.method_steps.all()}
    candidates: set[tuple[str, str, bool]] = set()
    for step in steps.values():
        for predecessor in step.predecessor_ids:
            if predecessor in steps:
                candidates.add((predecessor, step.external_id, False))
        for successor in step.successor_ids:
            if successor in steps:
                candidates.add((step.external_id, successor, False))
    # Only add ordering edges where a step has no explicitly declared predecessor.
    ordered = sorted(steps.values(), key=lambda value: value.order)
    for previous, current in zip(ordered, ordered[1:]):
        has_explicit_parent = any(target == current.external_id for _source, target, _inferred in candidates)
        if not has_explicit_parent:
            candidates.add((previous.external_id, current.external_id, True))
    with transaction.atomic():
        run.workflow_edges.all().delete()
        WorkflowEdge.objects.bulk_create([
            WorkflowEdge(extraction_run=run, source_step=steps[source], target_step=steps[target],
                         is_inferred=inferred, confidence=0.65 if inferred else 1.0)
            for source, target, inferred in candidates if source != target
        ])
    return list(run.workflow_edges.select_related("source_step", "target_step"))


def mermaid_diagram(run: ExtractionRun) -> str:
    lines = ["flowchart TD"]
    for step in run.method_steps.all():
        label = step.action.replace('"', "'")
        lines.append(f'    {step.external_id}["{label}"]')
    for edge in run.workflow_edges.select_related("source_step", "target_step"):
        connector = "-. inferred .->" if edge.is_inferred else "-->"
        lines.append(f"    {edge.source_step.external_id} {connector} {edge.target_step.external_id}")
    return "\n".join(lines)
