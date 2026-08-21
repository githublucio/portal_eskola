from django.contrib import admin
from django.utils import timezone

from .models import Event, PublishStatus


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "start_at", "end_at", "location", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "description", "location", "organizer")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "published_at")
    date_hierarchy = "start_at"
    actions = ("make_published", "make_draft", "make_archived")

    @admin.action(description="Marka hanesan publika")
    def make_published(self, request, queryset):
        now = timezone.now()
        for event in queryset:
            event.status = PublishStatus.PUBLISHED
            if event.published_at is None:
                event.published_at = now
            event.save(update_fields=["status", "published_at", "updated_at"])

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
