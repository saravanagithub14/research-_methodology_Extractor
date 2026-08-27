from django import forms

from .models import Paper


class PaperUploadForm(forms.ModelForm):
    class Meta:
        model = Paper
        fields = ("source_file",)

    def clean_source_file(self):
        uploaded = self.cleaned_data["source_file"]
        from django.conf import settings
        if not uploaded.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Please upload a PDF file.")
        if uploaded.size > settings.MAX_PDF_UPLOAD_BYTES:
            raise forms.ValidationError("The PDF exceeds the configured upload size limit.")
        if uploaded.read(5) != b"%PDF-":
            raise forms.ValidationError("The uploaded file is not a valid PDF.")
        uploaded.seek(0)
        return uploaded
