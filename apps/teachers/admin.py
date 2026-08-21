from django.contrib import admin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "employee_number",
        "last_name",
        "first_name",
        "department",
        "status",
        "updated_at",
    )
    list_filter = ("status", "department")
    search_fields = (
        "employee_number",
        "first_name",
        "last_name",
        "email",
        "specialization",
        "qualification",
    )
    autocomplete_fields = ("department", "user")
    readonly_fields = ("created_at", "updated_at")
