from django.contrib import admin
from django.utils import timezone

from .models import AcademicYear, Course, Department, PublishStatus, Subject


class SubjectInline(admin.TabularInline):
    model = Subject
    extra = 1
    fields = ("code", "name", "semester", "credits", "is_active")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "description")


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    actions = ("make_active",)

    @admin.action(description="Ativar ano académico selecionado")
    def make_active(self, request, queryset):
        year = queryset.order_by("-start_date").first()
        if not year:
            return
        AcademicYear.objects.filter(is_active=True).update(is_active=False)
        year.is_active = True
        year.save(update_fields=["is_active", "updated_at"])


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "status", "updated_at")
    list_filter = ("status", "department")
    search_fields = ("code", "name", "description", "qualification")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at", "published_at")
    inlines = (SubjectInline,)
    actions = ("make_published", "make_draft", "make_archived")

    @admin.action(description="Marka hanesan publika")
    def make_published(self, request, queryset):
        now = timezone.now()
        for course in queryset:
            course.status = PublishStatus.PUBLISHED
            if course.published_at is None:
                course.published_at = now
            course.save(update_fields=["status", "published_at", "updated_at"])

    @admin.action(description="Marka hanesan raskunhu")
    def make_draft(self, request, queryset):
        queryset.update(status=PublishStatus.DRAFT)

    @admin.action(description="Arquivar")
    def make_archived(self, request, queryset):
        queryset.update(status=PublishStatus.ARCHIVED)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "course", "semester", "credits", "is_active")
    list_filter = ("is_active", "course__department", "course")
    search_fields = ("code", "name", "course__name", "course__code")
