from django.db.models import Q
from django.views.generic import DetailView, ListView

from .models import News, NewsCategory, PublishStatus


class NewsListView(ListView):
    model = News
    template_name = "news/list.html"
    context_object_name = "news_list"
    paginate_by = 9

    def get_queryset(self):
        qs = (
            News.objects.filter(status=PublishStatus.PUBLISHED)
            .select_related("category", "author")
        )
        category_slug = self.request.GET.get("category")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(content__icontains=query)
            )
        announcement = self.request.GET.get("announcement")
        if announcement == "1":
            qs = qs.filter(is_announcement=True)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = NewsCategory.objects.all()
        context["active_category"] = self.request.GET.get("category", "")
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["announcement_only"] = self.request.GET.get("announcement") == "1"
        return context


class NewsDetailView(DetailView):
    model = News
    template_name = "news/detail.html"
    context_object_name = "news"
    slug_field = "slug"

    def get_queryset(self):
        return News.objects.filter(status=PublishStatus.PUBLISHED).select_related(
            "category", "author"
        )
