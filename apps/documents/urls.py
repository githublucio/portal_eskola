from django.urls import path

from .views import DocumentDownloadView, DocumentListView

app_name = "documents"

urlpatterns = [
    path("", DocumentListView.as_view(), name="list"),
    path("<slug:slug>/download/", DocumentDownloadView.as_view(), name="download"),
]
