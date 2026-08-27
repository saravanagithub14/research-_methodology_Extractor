from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("papers", "0001_initial")]
    operations = [
        migrations.AlterField(model_name="paper", name="status", field=models.CharField(choices=[("uploaded", "Uploaded"), ("parsing", "Parsing"), ("failed", "Failed"), ("parsed", "Parsed")], default="uploaded", max_length=32)),
        migrations.CreateModel(name="DocumentBlock", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("page_number", models.PositiveIntegerField()),
            ("block_type", models.CharField(choices=[("heading", "Heading"), ("paragraph", "Paragraph"), ("table", "Table"), ("caption", "Caption"), ("list", "List"), ("reference", "Reference"), ("unknown", "Unknown")], default="unknown", max_length=16)),
            ("heading", models.CharField(blank=True, max_length=500)), ("text", models.TextField()), ("order_index", models.PositiveIntegerField()), ("parser_metadata", models.JSONField(blank=True, default=dict)),
            ("paper", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="blocks", to="papers.paper")),
        ], options={"ordering": ("order_index",)}),
        migrations.AddConstraint(model_name="documentblock", constraint=models.UniqueConstraint(fields=("paper", "order_index"), name="unique_paper_block_order")),
    ]
