import mimetypes
from pathlib import Path

from django.db.models import Q
from django.http import FileResponse, Http404
from django.views.generic import DetailView, ListView

from .models import Document, DocumentCategory, PublishStatus


class DocumentListView(ListView):
    model = Document
    template_name = "documents/list.html"
    context_object_name = "documents"
    paginate_by = 12

    def get_queryset(self):
        qs = Document.objects.filter(
            status=PublishStatus.PUBLISHED,
            is_public=True,
        ).select_related("category")
        category_slug = self.request.GET.get("category")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(version__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = DocumentCategory.objects.all()
        context["active_category"] = self.request.GET.get("category", "")
        context["search_query"] = self.request.GET.get("q", "").strip()
        return context


class DocumentDownloadView(DetailView):
    model = Document
    slug_field = "slug"

    def get_queryset(self):
        return Document.objects.filter(
            status=PublishStatus.PUBLISHED,
            is_public=True,
        )

    def get(self, request, *args, **kwargs):
        document = self.get_object()
        if not document.file:
            raise Http404
        content_type, _ = mimetypes.guess_type(document.file.name)
        response = FileResponse(
            document.file.open("rb"),
            as_attachment=True,
            filename=Path(document.file.name).name,
            content_type=content_type or "application/octet-stream",
        )
        return response
