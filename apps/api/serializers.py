from rest_framework import serializers

from apps.courses.models import Course, Department, PublishStatus as CourseStatus, Subject
from apps.documents.models import Document, DocumentCategory, PublishStatus as DocStatus
from apps.events.models import Event, PublishStatus as EventStatus
from apps.news.models import News, NewsCategory, PublishStatus as NewsStatus


class NewsCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsCategory
        fields = ("id", "name", "slug")


class NewsSerializer(serializers.ModelSerializer):
    category = NewsCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=NewsCategory.objects.all(),
        source="category",
        write_only=True,
    )
    absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = (
            "id",
            "title",
            "slug",
            "category",
            "category_id",
            "summary",
            "content",
            "featured_image",
            "status",
            "is_announcement",
            "published_at",
            "created_at",
            "updated_at",
            "absolute_url",
        )
        read_only_fields = ("slug", "published_at", "created_at", "updated_at")

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()


class EventSerializer(serializers.ModelSerializer):
    absolute_url = serializers.SerializerMethodField()
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "location",
            "organizer",
            "start_at",
            "end_at",
            "image",
            "status",
            "published_at",
            "created_at",
            "updated_at",
            "absolute_url",
            "is_upcoming",
        )
        read_only_fields = ("slug", "published_at", "created_at", "updated_at")

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "code", "name")


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ("id", "code", "name", "credits", "semester", "is_active")


class CourseSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source="department",
        write_only=True,
    )
    subjects = SubjectSerializer(many=True, read_only=True)
    absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id",
            "code",
            "name",
            "slug",
            "department",
            "department_id",
            "description",
            "duration",
            "qualification",
            "requirements",
            "image",
            "status",
            "published_at",
            "subjects",
            "absolute_url",
        )
        read_only_fields = ("slug", "published_at")

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()


class DocumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = ("id", "name", "slug")


class DocumentSerializer(serializers.ModelSerializer):
    category = DocumentCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=DocumentCategory.objects.all(),
        source="category",
        write_only=True,
    )
    file_url = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "slug",
            "category",
            "category_id",
            "description",
            "file",
            "file_url",
            "version",
            "is_public",
            "status",
            "published_at",
            "created_at",
            "updated_at",
            "absolute_url",
        )
        read_only_fields = ("slug", "published_at", "created_at", "updated_at")
        extra_kwargs = {"file": {"write_only": True, "required": False}}

    def get_file_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return None
        # Private docs: only expose file URL to staff
        user = getattr(request, "user", None)
        if not obj.is_public and not (
            user and user.is_authenticated and (user.is_staff or user.is_superuser)
        ):
            return None
        url = obj.file.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()


# Re-export statuses for views/filters
__all__ = [
    "NewsSerializer",
    "EventSerializer",
    "CourseSerializer",
    "DocumentSerializer",
    "NewsStatus",
    "EventStatus",
    "CourseStatus",
    "DocStatus",
]
