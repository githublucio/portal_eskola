from django.contrib import admin
from django.utils import timezone

from .models import (
    ApplicationCriterion,
    ApplicationSettings,
    AttendanceRecord,
    Certificate,
    CertificateStatus,
    GradeEntry,
    Notification,
    OnlineApplication,
    TimetableSlot,
)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("date", "student", "classroom", "subject", "status", "recorded_by")
    list_filter = ("status", "date", "classroom")
    search_fields = (
        "student__student_number",
        "student__first_name",
        "student__last_name",
        "subject__code",
        "subject__name",
    )
    autocomplete_fields = ("student", "classroom", "subject", "recorded_by")
    date_hierarchy = "date"
    list_per_page = 50


@admin.register(GradeEntry)
class GradeEntryAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "subject",
        "classroom",
        "academic_year",
        "term",
        "score",
        "max_score",
        "assessment_name",
    )
    list_filter = ("academic_year", "term", "classroom")
    search_fields = (
        "student__student_number",
        "student__first_name",
        "student__last_name",
        "subject__code",
        "assessment_name",
    )
    autocomplete_fields = (
        "student",
        "subject",
        "classroom",
        "academic_year",
        "recorded_by",
    )
    list_per_page = 50


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = (
        "classroom",
        "weekday",
        "start_time",
        "end_time",
        "subject",
        "teacher",
        "room",
        "is_active",
    )
    list_filter = ("weekday", "is_active", "classroom")
    search_fields = ("subject__code", "subject__name", "room", "classroom__name")
    autocomplete_fields = ("classroom", "subject", "teacher")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        "certificate_number",
        "title",
        "student",
        "status",
        "issued_at",
        "academic_year",
    )
    list_filter = ("status", "academic_year")
    search_fields = (
        "certificate_number",
        "title",
        "student__student_number",
        "student__first_name",
        "student__last_name",
    )
    autocomplete_fields = ("student", "academic_year", "issued_by")
    actions = ("mark_issued",)

    @admin.action(description="Marka hanesan emite")
    def mark_issued(self, request, queryset):
        today = timezone.localdate()
        for cert in queryset:
            cert.status = CertificateStatus.ISSUED
            if cert.issued_at is None:
                cert.issued_at = today
            if not cert.issued_by_id:
                cert.issued_by = request.user
            cert.save()


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("title", "message", "user__username")
    autocomplete_fields = ("user",)


@admin.register(OnlineApplication)
class OnlineApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "desired_course",
        "status",
        "has_certificate",
        "created_at",
    )
    list_filter = ("status", "desired_course", "created_at")
    search_fields = ("full_name", "email", "phone", "desired_course_text")
    autocomplete_fields = ("desired_course",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(boolean=True, description="Sertifikadu")
    def has_certificate(self, obj):
        return bool(obj.certificate_file)


@admin.register(ApplicationSettings)
class ApplicationSettingsAdmin(admin.ModelAdmin):
    list_display = ("is_open", "min_age", "max_age", "opens_at", "closes_at", "updated_at")
    fields = (
        "is_open",
        "title",
        "intro",
        "closed_message",
        "min_age",
        "max_age",
        "opens_at",
        "closes_at",
        "updated_at",
    )
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not ApplicationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ApplicationCriterion)
class ApplicationCriterionAdmin(admin.ModelAdmin):
    list_display = ("text", "sort_order", "is_active", "updated_at")
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("text",)
    ordering = ("sort_order", "id")

