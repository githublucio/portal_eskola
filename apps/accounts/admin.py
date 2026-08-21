from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AuditLog, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "display_name",
        "is_staff",
        "is_active",
        "role_list",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "first_name", "last_name", "display_name")
    filter_horizontal = ("groups", "user_permissions")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Perfil", {"fields": ("display_name", "phone")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Perfil", {"fields": ("display_name", "phone", "groups")}),
    )

    @admin.display(description="Roles")
    def role_list(self, obj):
        return ", ".join(obj.role_names()) or "—"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "user",
        "action",
        "object_type",
        "object_repr",
        "ip_address",
    )
    list_filter = ("action", "object_type", "created_at")
    search_fields = (
        "user__username",
        "object_repr",
        "message",
        "object_type",
        "path",
    )
    readonly_fields = (
        "user",
        "action",
        "object_type",
        "object_id",
        "object_repr",
        "message",
        "ip_address",
        "path",
        "created_at",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
