from django.db import models
from django.utils import timezone
from papers.models import DocumentBlock, Paper


class ExtractionRun(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="extraction_runs")
    model = models.CharField(max_length=128)
    prompt_version = models.CharField(max_length=64, default="method_extraction_v1")
    schema_version = models.CharField(max_length=32, default="v1")
    status = models.CharField(max_length=16, default="pending")
    token_usage = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)


class ExtractedEntity(models.Model):
    run = models.ForeignKey(ExtractionRun, on_delete=models.CASCADE, related_name="entities")
    entity_type = models.CharField(max_length=64)
    original_name = models.CharField(max_length=500)
    normalized_name = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=16, default="reported")
    attributes = models.JSONField(default=dict)


class EvidenceReference(models.Model):
    entity = models.ForeignKey(ExtractedEntity, on_delete=models.CASCADE, related_name="evidence")
    block = models.ForeignKey(DocumentBlock, on_delete=models.PROTECT, related_name="evidence_references", null=True, blank=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    section = models.CharField(max_length=500, blank=True)
    quote = models.TextField()


class MethodStep(models.Model):
    extraction_run = models.ForeignKey(ExtractionRun, on_delete=models.CASCADE, related_name="method_steps")
    external_id = models.CharField(max_length=128)
    order = models.PositiveIntegerField()
    category = models.CharField(max_length=128)
    action = models.CharField(max_length=500)
    description = models.TextField()
    inputs = models.JSONField(default=list)
    outputs = models.JSONField(default=list)
    parameters = models.JSONField(default=dict)
    duration = models.CharField(max_length=128, blank=True)
    temperature = models.CharField(max_length=128, blank=True)
    predecessor_ids = models.JSONField(default=list)
    successor_ids = models.JSONField(default=list)
    confidence = models.FloatField()

    class Meta:
        ordering = ("order",)
        constraints = [models.UniqueConstraint(fields=("extraction_run", "external_id"), name="unique_run_step_id")]


class MethodStepEvidence(models.Model):
    method_step = models.ForeignKey(MethodStep, on_delete=models.CASCADE, related_name="evidence")
    block = models.ForeignKey(DocumentBlock, on_delete=models.PROTECT, null=True, blank=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    section = models.CharField(max_length=500, blank=True)
    quote = models.TextField()


class WorkflowEdge(models.Model):
    extraction_run = models.ForeignKey(ExtractionRun, on_delete=models.CASCADE, related_name="workflow_edges")
    source_step = models.ForeignKey(MethodStep, on_delete=models.CASCADE, related_name="outgoing_edges")
    target_step = models.ForeignKey(MethodStep, on_delete=models.CASCADE, related_name="incoming_edges")
    is_inferred = models.BooleanField(default=False)
    confidence = models.FloatField(default=1.0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("extraction_run", "source_step", "target_step"), name="unique_workflow_edge")]


class ReproducibilityAssessment(models.Model):
    extraction_run = models.OneToOneField(ExtractionRun, on_delete=models.CASCADE, related_name="reproducibility_assessment")
    score = models.PositiveSmallIntegerField()
    reported = models.JSONField(default=list)
    missing = models.JSONField(default=list)
    ambiguous = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    rubric_version = models.CharField(max_length=32, default="rna_seq_v1")


class AIUsageLog(models.Model):
    class Tier(models.TextChoices):
        FLAGSHIP = "flagship", "Flagship"
        MINI_NANO = "mini_nano", "Mini / Nano"

    extraction_run = models.ForeignKey(ExtractionRun, on_delete=models.CASCADE, related_name="usage_logs")
    model = models.CharField(max_length=128)
    tier = models.CharField(max_length=16, choices=Tier.choices)
    estimated_input_tokens = models.PositiveIntegerField()
    estimated_output_tokens = models.PositiveIntegerField()
    actual_input_tokens = models.PositiveIntegerField(null=True, blank=True)
    actual_output_tokens = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
