from django.contrib import admin
from django.utils import timezone

from .models import News, NewsCategory, PublishStatus


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "status",
        "is_announcement",
        "published_at",
        "updated_at",
    )
    list_filter = ("status", "is_announcement", "category")
    search_fields = ("title", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "published_at")
    date_hierarchy = "published_at"
    actions = ("make_published", "make_draft", "make_archived")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "summary",
                    "content",
                    "featured_image",
                    "status",
                    "is_announcement",
                )
            },
        ),
        (
            "Meta",
            {"fields": ("author", "published_at", "created_at", "updated_at")},
        ),
    )

    @admin.action(description="Marka hanesan publika")
    def make_published(self, request, queryset):
        now = timezone.now()
        for item in queryset:
            item.status = PublishStatus.PUBLISHED
            if item.published_at is None:
                item.published_at = now
            item.save(update_fields=["status", "published_at", "updated_at"])

    @admin.action(description="Marka hanesan raskunhu")
    def make_draft(self, request, queryset):
        queryset.update(status=PublishStatus.DRAFT)

    @admin.action(description="Arquivar")
    def make_archived(self, request, queryset):
        queryset.update(status=PublishStatus.ARCHIVED)

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)
