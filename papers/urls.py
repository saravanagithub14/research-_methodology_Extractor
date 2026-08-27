from django.urls import path

from . import views

app_name = "papers"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("papers/upload/", views.upload_paper, name="upload"),
    path("papers/<uuid:paper_id>/", views.paper_detail, name="detail"),
    path("papers/<uuid:paper_id>/sections/", views.paper_sections, name="sections"),
    path("papers/<uuid:paper_id>/sections/<int:section_id>/", views.section_evidence, name="section-evidence"),
    path("papers/<uuid:paper_id>/parse/", views.parse_paper_view, name="parse"),
    path("papers/<uuid:paper_id>/extract/", views.extract_paper_view, name="extract"),
    path("papers/<uuid:paper_id>/results/", views.paper_results, name="results"),
]
