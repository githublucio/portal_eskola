from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import Event, PublishStatus


class EventListView(ListView):
    model = Event
    template_name = "events/list.html"
    context_object_name = "events"
    paginate_by = 9

    def get_queryset(self):
        qs = Event.objects.filter(status=PublishStatus.PUBLISHED)
        scope = self.request.GET.get("scope", "upcoming")
        now = timezone.now()
        if scope == "past":
            qs = qs.filter(start_at__lt=now).order_by("-start_at")
        else:
            qs = qs.filter(start_at__gte=now).order_by("start_at")
            scope = "upcoming"
        self.scope = scope
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["scope"] = getattr(self, "scope", "upcoming")
        return context


class EventDetailView(DetailView):
    model = Event
    template_name = "events/detail.html"
    context_object_name = "event"
    slug_field = "slug"

    def get_queryset(self):
        return Event.objects.filter(status=PublishStatus.PUBLISHED)
