"""Deterministic reporting-completeness rubric for RNA-seq methodology."""
from __future__ import annotations

from extraction.models import ExtractionRun, ReproducibilityAssessment

RUBRIC = {
    "RNA extraction method": ("reagent", ("trizol", "rna extraction", "rneq", "mirvana")),
    "Library preparation": ("reagent", ("library prep", "nebnext", "trueseq")),
    "Sequencing platform": ("instrument", ("illumina", "novaseq", "nextseq", "miseq", "sequenc")),
    "Quality-control software": ("software", ("fastqc", "multiqc")),
    "Read preprocessing software": ("software", ("cutadapt", "trimmomatic", "fastp")),
    "Alignment software": ("software", ("star", "hisat", "bowtie")),
    "Quantification method": ("software", ("featurecounts", "salmon", "htseq", "rsem")),
    "Differential-expression method": ("software", ("deseq", "edger", "limma")),
    "Statistical method": ("statistical_method", ("test", "wald", "anova", "regression")),
    "Multiple-testing correction": ("statistical_method", ("fdr", "benjamini", "bonferroni")),
    "Data accession": ("dataset", ("geo", "sra", "ena", "gse", "prjna")),
}


def assess_reproducibility(run: ExtractionRun) -> ReproducibilityAssessment:
    entities = list(run.entities.all())
    reported, missing, ambiguous = [], [], []
    for label, (entity_type, keywords) in RUBRIC.items():
        matches = [entity for entity in entities if entity.entity_type == entity_type and any(keyword in entity.original_name.lower() for keyword in keywords)]
        if any(entity.status == "reported" for entity in matches):
            reported.append(label)
        elif matches:
            ambiguous.append(label)
        else:
            missing.append(label)
    total = len(RUBRIC)
    score = round(100 * len(reported) / total) if total else 0
    recommendations = [f"Report {item.lower()}." for item in missing]
    assessment, _created = ReproducibilityAssessment.objects.update_or_create(
        extraction_run=run,
        defaults={"score": score, "reported": reported, "missing": missing, "ambiguous": ambiguous, "recommendations": recommendations},
    )
    return assessment
