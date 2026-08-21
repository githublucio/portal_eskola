from django.contrib import admin
from django.utils import timezone

from .models import Page, PublishStatus


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "status", "published_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "slug", "content", "seo_title")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "published_at")
    actions = ("make_published", "make_draft", "make_archived")

    fieldsets = (
        (None, {"fields": ("title", "slug", "content", "image", "status")}),
        ("SEO", {"fields": ("seo_title", "seo_description")}),
        (
            "Meta",
            {"fields": ("author", "published_at", "created_at", "updated_at")},
        ),
    )

    @admin.action(description="Marka hanesan publika")
    def make_published(self, request, queryset):
        now = timezone.now()
        for page in queryset:
            page.status = PublishStatus.PUBLISHED
            if page.published_at is None:
                page.published_at = now
            page.save(update_fields=["status", "published_at", "updated_at"])

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
