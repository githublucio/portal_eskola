from django.db.models import Q
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Course, PublishStatus as CourseStatus
from apps.documents.models import Document, PublishStatus as DocStatus
from apps.events.models import Event, PublishStatus as EventStatus
from apps.news.models import News, PublishStatus as NewsStatus

from .permissions import ReadOnlyOrDjangoModelPermissions
from .serializers import (
    CourseSerializer,
    DocumentSerializer,
    EventSerializer,
    NewsSerializer,
)


class ApiRootView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(
            {
                "version": "v1",
                "endpoints": {
                    "news": request.build_absolute_uri("/api/v1/news/"),
                    "events": request.build_absolute_uri("/api/v1/events/"),
                    "courses": request.build_absolute_uri("/api/v1/courses/"),
                    "documents": request.build_absolute_uri("/api/v1/documents/"),
                    "auth_token": request.build_absolute_uri("/api/v1/auth/token/"),
                    "me": request.build_absolute_uri("/api/v1/auth/me/"),
                },
            }
        )


class MeView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.pk,
                "username": user.get_username(),
                "email": user.email,
                "display_name": user.public_name,
                "is_staff": user.is_staff,
                "roles": user.role_names(),
            }
        )


class PublishedQuerysetMixin:
    """Anonymous users see published content only; staff can see all with ?all=1."""

    published_status = None
    public_filter = None

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        show_all = (
            self.request.query_params.get("all") == "1"
            and user.is_authenticated
            and (user.is_staff or user.is_superuser)
        )
        if show_all:
            return qs
        qs = qs.filter(status=self.published_status)
        if self.public_filter:
            qs = qs.filter(**self.public_filter)
        return qs


class NewsViewSet(PublishedQuerysetMixin, viewsets.ModelViewSet):
    queryset = News.objects.select_related("category").all()
    serializer_class = NewsSerializer
    permission_classes = [ReadOnlyOrDjangoModelPermissions]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    lookup_field = "slug"
    published_status = NewsStatus.PUBLISHED
    search_fields = ["title", "summary", "content"]
    filterset_fields = ["is_announcement", "category__slug"]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(summary__icontains=q)
                | Q(content__icontains=q)
            )
        announcement = self.request.query_params.get("announcement")
        if announcement in {"1", "true", "yes"}:
            qs = qs.filter(is_announcement=True)
        category = self.request.query_params.get("category", "").strip()
        if category:
            qs = qs.filter(category__slug=category)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class EventViewSet(PublishedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [ReadOnlyOrDjangoModelPermissions]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    lookup_field = "slug"
    published_status = EventStatus.PUBLISHED

    def get_queryset(self):
        qs = super().get_queryset()
        scope = self.request.query_params.get("scope", "").strip()
        from django.utils import timezone

        now = timezone.now()
        if scope == "upcoming":
            qs = qs.filter(start_at__gte=now).order_by("start_at")
        elif scope == "past":
            qs = qs.filter(start_at__lt=now).order_by("-start_at")
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CourseViewSet(PublishedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Course.objects.select_related("department").prefetch_related("subjects")
    serializer_class = CourseSerializer
    permission_classes = [ReadOnlyOrDjangoModelPermissions]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    lookup_field = "slug"
    published_status = CourseStatus.PUBLISHED

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(code__icontains=q)
                | Q(description__icontains=q)
            )
        department = self.request.query_params.get("department", "").strip()
        if department:
            qs = qs.filter(department__code__iexact=department)
        return qs


class DocumentViewSet(PublishedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Document.objects.select_related("category").all()
    serializer_class = DocumentSerializer
    permission_classes = [ReadOnlyOrDjangoModelPermissions]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    lookup_field = "slug"
    published_status = DocStatus.PUBLISHED
    public_filter = {"is_public": True}

    def get_queryset(self):
        qs = super().get_queryset()
        # Staff with all=1 already handled; for authenticated staff without all=1,
        # still hide private from public default — keep public_filter.
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        return qs

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
