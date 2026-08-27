from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("extraction", "0004_workflowedge")]
    operations = [migrations.CreateModel(name="ReproducibilityAssessment", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("score", models.PositiveSmallIntegerField()),
        ("reported", models.JSONField(default=list)), ("missing", models.JSONField(default=list)), ("ambiguous", models.JSONField(default=list)), ("recommendations", models.JSONField(default=list)), ("rubric_version", models.CharField(default="rna_seq_v1", max_length=32)),
        ("extraction_run", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="reproducibility_assessment", to="extraction.extractionrun")),
    ])]
