from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("extraction", "0003_methodstep_methodstepevidence")]
    operations = [migrations.CreateModel(name="WorkflowEdge", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("is_inferred", models.BooleanField(default=False)), ("confidence", models.FloatField(default=1.0)),
        ("extraction_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workflow_edges", to="extraction.extractionrun")),
        ("source_step", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="outgoing_edges", to="extraction.methodstep")),
        ("target_step", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incoming_edges", to="extraction.methodstep")),
    ]), migrations.AddConstraint(model_name="workflowedge", constraint=models.UniqueConstraint(fields=("extraction_run", "source_step", "target_step"), name="unique_workflow_edge"))]
