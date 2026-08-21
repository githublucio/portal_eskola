from django.db.models import Q
from django.views.generic import DetailView, ListView

from .models import Course, Department, PublishStatus


class CourseListView(ListView):
    model = Course
    template_name = "courses/list.html"
    context_object_name = "courses"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Course.objects.filter(status=PublishStatus.PUBLISHED)
            .select_related("department")
            .prefetch_related("subjects")
        )
        department = self.request.GET.get("department", "").strip()
        q = self.request.GET.get("q", "").strip()
        if department:
            qs = qs.filter(department__code__iexact=department)
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(code__icontains=q)
                | Q(description__icontains=q)
                | Q(qualification__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["departments"] = Department.objects.filter(is_active=True)
        context["q"] = self.request.GET.get("q", "").strip()
        context["selected_department"] = self.request.GET.get("department", "").strip()
        return context


class CourseDetailView(DetailView):
    model = Course
    template_name = "courses/detail.html"
    context_object_name = "course"
    slug_field = "slug"

    def get_queryset(self):
        return (
            Course.objects.filter(status=PublishStatus.PUBLISHED)
            .select_related("department")
            .prefetch_related("subjects")
        )
