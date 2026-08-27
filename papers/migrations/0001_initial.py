# Generated manually for the initial Paper model.
import uuid

from django.db import migrations, models

import papers.models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Paper",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("source_file", models.FileField(upload_to=papers.models.paper_upload_path)),
                ("original_filename", models.CharField(max_length=255)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("page_count", models.PositiveIntegerField(blank=True, null=True)),
                ("status", models.CharField(choices=[("uploaded", "Uploaded"), ("parsing", "Parsing"), ("failed", "Failed")], default="uploaded", max_length=32)),
                ("parsing_metadata", models.JSONField(blank=True, default=dict)),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
    ]
