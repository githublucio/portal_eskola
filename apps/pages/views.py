from django.views.generic import DetailView

from .models import Page, PublishStatus


class PageDetailView(DetailView):
    model = Page
    template_name = "pages/detail.html"
    context_object_name = "page"
    slug_field = "slug"

    def get_queryset(self):
        return Page.objects.filter(status=PublishStatus.PUBLISHED)
