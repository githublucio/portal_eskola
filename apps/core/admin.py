from django.contrib import admin

from .models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {"fields": ("name", "short_name", "logo", "description")},
        ),
        ("História / Visão / Missão", {"fields": ("history", "vision", "mission")}),
        ("Kontaktu", {"fields": ("address", "phone", "email")}),
        (
            "Redes sociais",
            {"fields": ("facebook_url", "instagram_url", "youtube_url")},
        ),
        ("Mapa", {"fields": ("map_latitude", "map_longitude")}),
    )

    def has_add_permission(self, request):
        return not School.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
