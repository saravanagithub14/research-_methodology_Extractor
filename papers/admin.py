from django.contrib import admin

from .models import DocumentBlock, DocumentSection, Paper


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "status", "page_count", "uploaded_at")
    readonly_fields = ("id", "uploaded_at")


@admin.register(DocumentBlock)
class DocumentBlockAdmin(admin.ModelAdmin):
    list_display = ("paper", "page_number", "block_type", "order_index")
    list_filter = ("block_type",)
    search_fields = ("text", "heading")


@admin.register(DocumentSection)
class DocumentSectionAdmin(admin.ModelAdmin):
    list_display = ("paper", "section_name", "normalized_section_type", "start_page", "end_page", "confidence")
    list_filter = ("normalized_section_type",)
