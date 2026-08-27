from rest_framework import serializers

from .models import Paper


class PaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paper
        fields = ("id", "original_filename", "uploaded_at", "page_count", "status", "parsing_metadata")
