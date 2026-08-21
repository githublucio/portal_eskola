import csv

from django.http import HttpResponse
from django.utils import timezone
from django.views import View

from apps.academics.models import AttendanceRecord, GradeEntry, OnlineApplication
from apps.courses.models import Course
from apps.students.models import Enrollment, Student
from apps.teachers.models import Teacher

from .mixins import PermissionOrSuperuserMixin


class CsvReportMixin(PermissionOrSuperuserMixin, View):
    filename_prefix = "report"
    required_permissions: tuple[str, ...] = ()

    def get_rows(self):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        stamp = timezone.now().strftime("%Y%m%d_%H%M")
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="{self.filename_prefix}_{stamp}.csv"'
        )
        response.write("\ufeff")  # Excel-friendly UTF-8 BOM
        writer = csv.writer(response)
        for row in self.get_rows():
            writer.writerow(row)
        return response


class StudentsCsvReportView(CsvReportMixin):
    filename_prefix = "estudantes"
    required_permissions = ("students.view_student",)

    def get_rows(self):
        yield (
            "student_number",
            "first_name",
            "last_name",
            "status",
            "email",
            "phone",
        )
        for student in Student.objects.order_by("student_number"):
            yield (
                student.student_number,
                student.first_name,
                student.last_name,
                student.status,
                student.email,
                student.phone,
            )


class TeachersCsvReportView(CsvReportMixin):
    filename_prefix = "professores"
    required_permissions = ("teachers.view_teacher",)

    def get_rows(self):
        yield (
            "employee_number",
            "first_name",
            "last_name",
            "department",
            "status",
            "email",
            "specialization",
        )
        for teacher in Teacher.objects.select_related("department").order_by(
            "employee_number"
        ):
            yield (
                teacher.employee_number,
                teacher.first_name,
                teacher.last_name,
                teacher.department.code,
                teacher.status,
                teacher.email,
                teacher.specialization,
            )


class EnrollmentsCsvReportView(CsvReportMixin):
    filename_prefix = "matriculas"
    required_permissions = ("students.view_enrollment",)

    def get_rows(self):
        yield (
            "enrollment_number",
            "student_number",
            "student_name",
            "course_code",
            "academic_year",
            "enrollment_date",
            "status",
        )
        qs = Enrollment.objects.select_related(
            "student", "course", "academic_year"
        ).order_by("-enrollment_date")
        for item in qs:
            yield (
                item.enrollment_number,
                item.student.student_number,
                item.student.full_name,
                item.course.code,
                item.academic_year.name,
                item.enrollment_date.isoformat(),
                item.status,
            )


class CoursesCsvReportView(CsvReportMixin):
    filename_prefix = "cursos"
    required_permissions = ("courses.view_course",)

    def get_rows(self):
        yield ("code", "name", "department", "status", "qualification", "duration")
        for course in Course.objects.select_related("department").order_by("code"):
            yield (
                course.code,
                course.name,
                course.department.code,
                course.status,
                course.qualification,
                course.duration,
            )


class AttendanceCsvReportView(CsvReportMixin):
    filename_prefix = "assiduidade"
    required_permissions = ("academics.view_attendancerecord",)

    def get_rows(self):
        yield (
            "date",
            "student_number",
            "student_name",
            "classroom",
            "subject",
            "status",
            "recorded_by",
        )
        qs = AttendanceRecord.objects.select_related(
            "student", "classroom", "subject", "recorded_by"
        ).order_by("-date", "student__last_name")
        for row in qs:
            yield (
                row.date.isoformat(),
                row.student.student_number,
                row.student.full_name,
                row.classroom.name,
                row.subject.code,
                row.status,
                row.recorded_by.full_name if row.recorded_by_id else "",
            )


class GradesCsvReportView(CsvReportMixin):
    filename_prefix = "notas"
    required_permissions = ("academics.view_gradeentry",)

    def get_rows(self):
        yield (
            "student_number",
            "student_name",
            "subject",
            "classroom",
            "academic_year",
            "term",
            "assessment",
            "score",
            "max_score",
        )
        qs = GradeEntry.objects.select_related(
            "student", "subject", "classroom", "academic_year"
        ).order_by("-academic_year__start_date", "student__last_name")
        for row in qs:
            yield (
                row.student.student_number,
                row.student.full_name,
                row.subject.code,
                row.classroom.name,
                row.academic_year.name,
                row.term,
                row.assessment_name,
                row.score,
                row.max_score,
            )


class ApplicationsCsvReportView(CsvReportMixin):
    filename_prefix = "candidaturas"
    required_permissions = ("academics.view_onlineapplication",)

    def get_rows(self):
        yield (
            "full_name",
            "email",
            "phone",
            "desired_course",
            "status",
            "created_at",
        )
        qs = OnlineApplication.objects.select_related("desired_course").order_by(
            "-created_at"
        )
        for row in qs:
            course = ""
            if row.desired_course_id:
                course = row.desired_course.code
            elif row.desired_course_text:
                course = row.desired_course_text
            yield (
                row.full_name,
                row.email,
                row.phone,
                course,
                row.status,
                row.created_at.isoformat(),
            )
