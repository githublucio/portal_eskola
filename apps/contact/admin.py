from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "name",
        "email",
        "is_read",
        "reply_status",
        "created_at",
    )
    list_filter = ("is_read", "reply_status", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "phone", "subject", "message", "created_at")
    list_editable = ("is_read", "reply_status")
