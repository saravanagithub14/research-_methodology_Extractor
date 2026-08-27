from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("extraction", "0001_initial")]
    operations = [migrations.CreateModel(name="AIUsageLog", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("model", models.CharField(max_length=128)), ("tier", models.CharField(choices=[("flagship", "Flagship"), ("mini_nano", "Mini / Nano")], max_length=16)),
        ("estimated_input_tokens", models.PositiveIntegerField()), ("estimated_output_tokens", models.PositiveIntegerField()),
        ("actual_input_tokens", models.PositiveIntegerField(blank=True, null=True)), ("actual_output_tokens", models.PositiveIntegerField(blank=True, null=True)),
        ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
        ("extraction_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="usage_logs", to="extraction.extractionrun")),
    ])]
