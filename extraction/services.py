import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from openai import OpenAI
from papers.models import DocumentBlock, Paper
from .models import AIUsageLog, EvidenceReference, ExtractedEntity, ExtractionRun
from .prompts import METHOD_EXTRACTION_PROMPT_V2
from .schemas import MethodologyExtraction


def _strict_schema(schema: dict[str, object]) -> dict[str, object]:
    """Adapt Pydantic's nullable schema to OpenAI Structured Outputs strict mode."""
    if isinstance(schema.get("properties"), dict):
        properties = schema["properties"]
        # OpenAI strict JSON Schema does not accept this free-form dictionary
        # shape reliably. It remains a persisted/Pydantic field with an empty
        # default; later extraction passes can populate explicit parameters.
        properties.pop("parameters", None)
        schema["required"] = list(properties)
        for value in properties.values():
            if isinstance(value, dict):
                _strict_schema(value)
    if isinstance(schema.get("$defs"), dict):
        for value in schema["$defs"].values():
            if isinstance(value, dict):
                _strict_schema(value)
    if isinstance(schema.get("items"), dict):
        _strict_schema(schema["items"])
    return schema


def extract_methodology(blocks: list[dict[str, object]]) -> MethodologyExtraction:
    if not settings.OPENAI_API_KEY:
        raise ImproperlyConfigured("OPENAI_API_KEY is required for methodology extraction.")
    merged = {"software": [], "instruments": [], "reagents": [], "datasets": [], "statistical_methods": [], "method_steps": []}
    batch_size = settings.EXTRACTION_BLOCK_BATCH_SIZE
    batches = [blocks[start:start + batch_size] for start in range(0, len(blocks), batch_size)]
    def extract_batch(batch):
        response = OpenAI(api_key=settings.OPENAI_API_KEY).responses.create(
            model=settings.OPENAI_EXTRACTION_MODEL, instructions=METHOD_EXTRACTION_PROMPT_V2,
            input=json.dumps({"blocks": batch}),
            text={"format": {"type": "json_schema", "name": "methodology_extraction", "strict": True, "schema": _strict_schema(MethodologyExtraction.model_json_schema())}},
        )
        return MethodologyExtraction.model_validate_json(response.output_text)
    with ThreadPoolExecutor(max_workers=min(settings.EXTRACTION_MAX_CONCURRENCY, len(batches))) as executor:
        results = list(executor.map(extract_batch, batches))
    for result in results:
        for field in merged:
            merged[field].extend(getattr(result, field))
    for order, step in enumerate(merged["method_steps"], start=1):
        step.order = order
        step.id = f"step_{order}"
    return MethodologyExtraction.model_validate(merged)


def _tier(model: str) -> str:
    return AIUsageLog.Tier.MINI_NANO if "mini" in model or "nano" in model else AIUsageLog.Tier.FLAGSHIP


def _reserve_usage(run: ExtractionRun, input_text: str, batch_count: int) -> AIUsageLog:
    tier = _tier(run.model)
    estimated_input, estimated_output = max(1, len(input_text) // 4), 1000 * batch_count
    limit = 2_500_000 if tier == AIUsageLog.Tier.MINI_NANO else 250_000
    daily_total = AIUsageLog.objects.filter(tier=tier, created_at__gte=timezone.now() - timedelta(days=1)).aggregate(total=Sum("estimated_input_tokens") + Sum("estimated_output_tokens"))["total"] or 0
    if daily_total + estimated_input + estimated_output > limit:
        raise ImproperlyConfigured(f"Daily {tier} token allowance would be exceeded; external call was blocked.")
    return AIUsageLog.objects.create(extraction_run=run, model=run.model, tier=tier, estimated_input_tokens=estimated_input, estimated_output_tokens=estimated_output)


def run_entity_extraction(paper: Paper) -> ExtractionRun:
    """Extract entities only from persisted, detected sections and persist their evidence."""
    selected_indexes: set[int] = set()
    for section in paper.sections.select_related("start_block", "end_block"):
        selected_indexes.update(range(section.start_block.order_index, section.end_block.order_index + 1))
    blocks = list(paper.blocks.filter(order_index__in=selected_indexes)) if selected_indexes else list(paper.blocks.all())
    blocks = [block for block in blocks if _is_method_block(block.text)]
    payload = [{"id": str(block.id), "page": block.page_number, "text": block.text} for block in blocks]
    serialized_payload = json.dumps(payload)
    with transaction.atomic():
        run = ExtractionRun.objects.create(paper=paper, model=settings.OPENAI_EXTRACTION_MODEL, status="running")
        usage = _reserve_usage(run, serialized_payload, max(1, (len(payload) + settings.EXTRACTION_BLOCK_BATCH_SIZE - 1) // settings.EXTRACTION_BLOCK_BATCH_SIZE))
    try:
        result = extract_methodology(payload)
        _persist_entities(run, result, {str(block.id): block for block in blocks})
        from extraction.procedure import persist_method_steps
        from extraction.workflow import build_workflow
        persist_method_steps(run, result.method_steps)
        build_workflow(run)
    except Exception as error:
        run.status, run.error = "failed", str(error)[:2000]
        run.save(update_fields=("status", "error"))
        raise
    run.status = "completed"
    run.token_usage = {"estimated_input": usage.estimated_input_tokens, "estimated_output": usage.estimated_output_tokens}
    run.save(update_fields=("status", "token_usage"))
    return run


def _is_method_block(text: str) -> bool:
    value = text.strip()
    if not value or value.startswith("Downloaded from"):
        return False
    if re.fullmatch(r"[\d\s.%()+\-–—]+", value):
        return False
    # Bibliography-style author/year entries are cited work, not this paper's method.
    if re.match(r"^[A-Z][A-Za-z'\-]+,.*\(\d{4}\)", value):
        return False
    return True


def _persist_entities(run: ExtractionRun, result: MethodologyExtraction, block_map: dict[str, DocumentBlock]) -> None:
    for entity_type, entities in (("software", result.software), ("instrument", result.instruments), ("reagent", result.reagents), ("dataset", result.datasets), ("statistical_method", result.statistical_methods)):
        for entity in entities:
            values = entity.model_dump(exclude={"evidence", "name", "status"})
            name = getattr(entity, "name", None) or getattr(entity, "accession", None) or "Unnamed dataset"
            record = ExtractedEntity.objects.create(run=run, entity_type=entity_type, original_name=name, status=getattr(entity, "status", "reported"), attributes=values)
            for evidence in entity.evidence:
                EvidenceReference.objects.create(entity=record, block=block_map.get(evidence.block_id or ""), page_number=evidence.page, section=evidence.section or "", quote=evidence.quote)
