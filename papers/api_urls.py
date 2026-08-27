from django.urls import path

from .api_views import PaperDetailView, PaperListCreateView, paper_export, paper_methods, paper_reproducibility, paper_sections, paper_workflow

urlpatterns = [
    path("papers/", PaperListCreateView.as_view(), name="paper-list"),
    path("papers/<uuid:pk>/", PaperDetailView.as_view(), name="paper-detail"),
    path("papers/<uuid:pk>/sections/", paper_sections),
    path("papers/<uuid:pk>/methods/", paper_methods),
    path("papers/<uuid:pk>/workflow/", paper_workflow),
    path("papers/<uuid:pk>/reproducibility/", paper_reproducibility),
    path("papers/<uuid:pk>/export/json/", paper_export),
]
