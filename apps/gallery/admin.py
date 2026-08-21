from django.contrib import admin
from django.utils import timezone

from .models import GalleryAlbum, GalleryPhoto, PublishStatus


class GalleryPhotoInline(admin.TabularInline):
    model = GalleryPhoto
    extra = 1
    fields = ("image", "caption", "sort_order")


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "event", "published_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "published_at")
    inlines = [GalleryPhotoInline]
    actions = ("make_published", "make_draft", "make_archived")

    @admin.action(description="Marka hanesan publika")
    def make_published(self, request, queryset):
        now = timezone.now()
        for album in queryset:
            album.status = PublishStatus.PUBLISHED
            if album.published_at is None:
                album.published_at = now
            album.save(update_fields=["status", "published_at", "updated_at"])

    @admin.action(description="Marka hanesan raskunhu")
    def make_draft(self, request, queryset):
        queryset.update(status=PublishStatus.DRAFT)

    @admin.action(description="Arquivar")
    def make_archived(self, request, queryset):
        queryset.update(status=PublishStatus.ARCHIVED)


@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    list_display = ("album", "caption", "sort_order", "created_at")
    list_filter = ("album",)
    search_fields = ("caption", "album__title")
