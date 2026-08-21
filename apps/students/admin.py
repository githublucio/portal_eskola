from django.contrib import admin
from django.utils.html import format_html

from .models import ClassRoom, Enrollment, Student, StudentClass


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = (
        "enrollment_number",
        "course",
        "academic_year",
        "enrollment_date",
        "status",
    )
    autocomplete_fields = ("course", "academic_year")
    show_change_link = True
    ordering = ("-enrollment_date",)


class StudentClassInline(admin.TabularInline):
    model = StudentClass
    extra = 0
    fields = (
        "classroom",
        "academic_year",
        "status",
        "assigned_at",
        "left_at",
    )
    autocomplete_fields = ("classroom", "academic_year")
    show_change_link = True
    ordering = ("-assigned_at",)


class StudentAssignmentInline(admin.TabularInline):
    model = StudentClass
    extra = 0
    fields = ("student", "status", "assigned_at", "left_at")
    autocomplete_fields = ("student",)
    show_change_link = True


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "student_number",
        "last_name",
        "first_name",
        "status",
        "current_course_display",
        "current_class_display",
        "phone",
        "updated_at",
    )
    list_filter = ("status", "gender")
    search_fields = (
        "student_number",
        "first_name",
        "last_name",
        "email",
        "phone",
        "guardian_name",
        "enrollments__enrollment_number",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25
    inlines = (EnrollmentInline, StudentClassInline)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "student_number",
                    "first_name",
                    "last_name",
                    "status",
                    "user",
                    "photo",
                )
            },
        ),
        (
            "Kontaktu",
            {"fields": ("email", "phone", "address", "date_of_birth", "gender")},
        ),
        (
            "Encarregado",
            {"fields": ("guardian_name", "guardian_phone")},
        ),
        (
            "Notas",
            {"fields": ("notes", "created_at", "updated_at")},
        ),
    )

    @admin.display(description="Curso atual")
    def current_course_display(self, obj):
        enrollment = obj.current_enrollment()
        if not enrollment:
            return "—"
        return enrollment.course.code

    @admin.display(description="Turma atual")
    def current_class_display(self, obj):
        assignment = obj.current_class()
        if not assignment:
            return "—"
        return assignment.classroom.name


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "enrollment_number",
        "student",
        "course",
        "academic_year",
        "enrollment_date",
        "status",
        "updated_at",
    )
    list_filter = ("status", "academic_year", "course__department", "course")
    search_fields = (
        "enrollment_number",
        "student__student_number",
        "student__first_name",
        "student__last_name",
        "course__code",
        "course__name",
    )
    autocomplete_fields = ("student", "course", "academic_year")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "enrollment_date"
    list_per_page = 25
    list_select_related = ("student", "course", "academic_year")


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "course",
        "academic_year",
        "level",
        "capacity",
        "occupancy_display",
        "adviser",
        "is_active",
    )
    list_filter = ("is_active", "academic_year", "course__department", "level")
    search_fields = (
        "name",
        "course__code",
        "course__name",
        "adviser__first_name",
        "adviser__last_name",
        "adviser__employee_number",
    )
    autocomplete_fields = ("course", "academic_year", "adviser")
    readonly_fields = ("created_at", "updated_at", "occupancy_display")
    list_per_page = 25
    inlines = (StudentAssignmentInline,)
    list_select_related = ("course", "academic_year", "adviser")

    @admin.display(description="Okupasaun")
    def occupancy_display(self, obj):
        count = obj.enrolled_count
        color = "#0a5555" if count < obj.capacity else "#b00020"
        return format_html(
            '<span style="color:{};">{} / {}</span>',
            color,
            count,
            obj.capacity,
        )


@admin.register(StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "classroom",
        "academic_year",
        "status",
        "assigned_at",
        "left_at",
    )
    list_filter = ("status", "academic_year", "classroom__course")
    search_fields = (
        "student__student_number",
        "student__first_name",
        "student__last_name",
        "classroom__name",
        "classroom__course__code",
    )
    autocomplete_fields = ("student", "classroom", "academic_year")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "assigned_at"
    list_per_page = 25
    list_select_related = ("student", "classroom", "academic_year")
