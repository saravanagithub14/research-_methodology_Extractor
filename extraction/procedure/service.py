"""Persistence and validation boundary for ordered procedure reconstruction."""
from __future__ import annotations

from django.db import transaction

from extraction.models import ExtractionRun, MethodStep, MethodStepEvidence
from extraction.schemas import MethodStep as MethodStepSchema
from papers.models import DocumentBlock


def persist_method_steps(run: ExtractionRun, steps: list[MethodStepSchema]) -> list[MethodStep]:
    """Replace a run's steps only after all supplied source evidence validates."""
    deduplicated: list[MethodStepSchema] = []
    seen_actions: set[str] = set()
    for step in steps:
        action_key = " ".join(step.action.lower().split())
        if action_key not in seen_actions:
            seen_actions.add(action_key)
            deduplicated.append(step)
    steps = deduplicated[:15]
    for order, step in enumerate(steps, start=1):
        step.order = order
        step.id = f"step_{order}"
    if [step.order for step in steps] != list(range(1, len(steps) + 1)):
        raise ValueError("Method steps must use consecutive order values starting at 1.")
    block_ids = {str(block.id): block for block in DocumentBlock.objects.filter(paper=run.paper)}
    for step in steps:
        for evidence in step.evidence:
            if evidence.block_id and evidence.block_id not in block_ids:
                raise ValueError("Method-step evidence must reference a block from the same paper.")
    with transaction.atomic():
        run.method_steps.all().delete()
        records = [MethodStep(extraction_run=run, external_id=step.id, order=step.order, category=step.category,
                              action=step.action, description=step.description, inputs=step.inputs, outputs=step.outputs,
                              parameters=step.parameters, duration=step.duration or "", temperature=step.temperature or "",
                              predecessor_ids=step.predecessor_ids, successor_ids=step.successor_ids, confidence=step.confidence)
                   for step in steps]
        MethodStep.objects.bulk_create(records)
        records_by_id = {record.external_id: record for record in run.method_steps.all()}
        evidence_rows = []
        for step in steps:
            for evidence in step.evidence:
                evidence_rows.append(MethodStepEvidence(method_step=records_by_id[step.id], block=block_ids.get(evidence.block_id or ""),
                                                        page_number=evidence.page, section=evidence.section or "", quote=evidence.quote))
        MethodStepEvidence.objects.bulk_create(evidence_rows)
    return list(run.method_steps.all())
