from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("extraction", "0002_aiusagelog")]
    operations = [
        migrations.CreateModel(name="MethodStep", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("external_id", models.CharField(max_length=128)), ("order", models.PositiveIntegerField()), ("category", models.CharField(max_length=128)), ("action", models.CharField(max_length=500)), ("description", models.TextField()), ("inputs", models.JSONField(default=list)), ("outputs", models.JSONField(default=list)), ("parameters", models.JSONField(default=dict)), ("duration", models.CharField(blank=True, max_length=128)), ("temperature", models.CharField(blank=True, max_length=128)), ("predecessor_ids", models.JSONField(default=list)), ("successor_ids", models.JSONField(default=list)), ("confidence", models.FloatField()), ("extraction_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="method_steps", to="extraction.extractionrun"))], options={"ordering": ("order",)}),
        migrations.CreateModel(name="MethodStepEvidence", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("page_number", models.PositiveIntegerField(blank=True, null=True)), ("section", models.CharField(blank=True, max_length=500)), ("quote", models.TextField()), ("block", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="papers.documentblock")), ("method_step", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="evidence", to="extraction.methodstep"))]),
        migrations.AddConstraint(model_name="methodstep", constraint=models.UniqueConstraint(fields=("extraction_run", "external_id"), name="unique_run_step_id")),
    ]
