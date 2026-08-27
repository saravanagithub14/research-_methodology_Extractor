from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("papers", "0002_documentblock_paper_status_parsed")]
    operations = [
        migrations.CreateModel(name="DocumentSection", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("section_name", models.CharField(max_length=500)),
            ("normalized_section_type", models.CharField(max_length=64)),
            ("start_page", models.PositiveIntegerField()), ("end_page", models.PositiveIntegerField()),
            ("confidence", models.FloatField()),
            ("end_block", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sections_ending", to="papers.documentblock")),
            ("paper", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sections", to="papers.paper")),
            ("start_block", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sections_starting", to="papers.documentblock")),
        ], options={"ordering": ("start_block__order_index",)}),
        migrations.AddConstraint(model_name="documentsection", constraint=models.UniqueConstraint(fields=("paper", "start_block"), name="unique_paper_section_start")),
    ]
