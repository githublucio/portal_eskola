from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.core.models import School
from apps.courses.models import AcademicYear, Course, Department, PublishStatus
from apps.teachers.models import Teacher

from .models import (
    ClassRoom,
    Enrollment,
    EnrollmentStatus,
    Student,
    StudentClass,
    StudentClassStatus,
    StudentStatus,
)


class StudentFixturesMixin:
    def setUp(self):
        self.dept = Department.objects.create(code="PES", name="Peska")
        self.year = AcademicYear.objects.create(
            name="2025/2026",
            start_date="2025-09-01",
            end_date="2026-07-31",
            is_active=True,
        )
        self.course = Course.objects.create(
            department=self.dept,
            code="PESKA",
            name="Técnico de Peska",
            slug="tecnico-peska",
            status=PublishStatus.PUBLISHED,
        )
        self.teacher = Teacher.objects.create(
            employee_number="T-100",
            first_name="Ana",
            last_name="Costa",
            department=self.dept,
        )
        self.student = Student.objects.create(
            student_number="s-200",
            first_name="João",
            last_name="Pereira",
            status=StudentStatus.ACTIVE,
        )
        self.classroom = ClassRoom.objects.create(
            course=self.course,
            academic_year=self.year,
            name="PESKA-A",
            level=1,
            capacity=2,
            adviser=self.teacher,
        )


class StudentModelTests(TestCase):
    def test_create_and_normalize_number(self):
        student = Student.objects.create(
            student_number="s-100",
            first_name="João",
            last_name="Pereira",
            status=StudentStatus.ACTIVE,
        )
        self.assertEqual(student.student_number, "S-100")
        self.assertEqual(student.full_name, "João Pereira")

    def test_student_data_not_on_public_pages(self):
        School.get_solo()
        Student.objects.create(
            student_number="S-999",
            first_name="Segredo",
            last_name="Estudante",
            email="segredo@example.com",
        )
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Segredo")
        self.assertNotContains(response, "segredo@example.com")


class EnrollmentTests(StudentFixturesMixin, TestCase):
    def test_auto_enrollment_number_and_history(self):
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
            academic_year=self.year,
            status=EnrollmentStatus.ACTIVE,
        )
        self.assertTrue(enrollment.enrollment_number.startswith("ENR-"))
        self.assertEqual(self.student.current_enrollment(), enrollment)

        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.save()
        next_year = AcademicYear.objects.create(
            name="2026/2027",
            start_date="2026-09-01",
            end_date="2027-07-31",
        )
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            academic_year=next_year,
            enrollment_number="ENR-CUSTOM-1",
            status=EnrollmentStatus.ACTIVE,
        )
        self.assertEqual(self.student.enrollments.count(), 2)

    def test_only_one_active_enrollment(self):
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            academic_year=self.year,
            enrollment_number="ENR-1",
            status=EnrollmentStatus.ACTIVE,
        )
        other_year = AcademicYear.objects.create(
            name="2026/2027",
            start_date="2026-09-01",
            end_date="2027-07-31",
        )
        dup = Enrollment(
            student=self.student,
            course=self.course,
            academic_year=other_year,
            enrollment_number="ENR-2",
            status=EnrollmentStatus.ACTIVE,
        )
        with self.assertRaises(ValidationError):
            dup.full_clean()


class ClassRoomTests(StudentFixturesMixin, TestCase):
    def test_assign_student_to_class(self):
        assignment = StudentClass.objects.create(
            student=self.student,
            classroom=self.classroom,
            academic_year=self.year,
            status=StudentClassStatus.ACTIVE,
        )
        self.assertEqual(self.student.current_class(), assignment)
        self.assertEqual(self.classroom.enrolled_count, 1)

    def test_capacity_enforced(self):
        StudentClass.objects.create(
            student=self.student,
            classroom=self.classroom,
            academic_year=self.year,
            status=StudentClassStatus.ACTIVE,
        )
        s2 = Student.objects.create(
            student_number="S-201",
            first_name="Maria",
            last_name="Silva",
        )
        StudentClass.objects.create(
            student=s2,
            classroom=self.classroom,
            academic_year=self.year,
            status=StudentClassStatus.ACTIVE,
        )
        s3 = Student.objects.create(
            student_number="S-202",
            first_name="Pedro",
            last_name="Alves",
        )
        over = StudentClass(
            student=s3,
            classroom=self.classroom,
            academic_year=self.year,
            status=StudentClassStatus.ACTIVE,
        )
        with self.assertRaises(ValidationError):
            over.full_clean()

    def test_year_must_match_classroom(self):
        other_year = AcademicYear.objects.create(
            name="2024/2025",
            start_date="2024-09-01",
            end_date="2025-07-31",
        )
        bad = StudentClass(
            student=self.student,
            classroom=self.classroom,
            academic_year=other_year,
            status=StudentClassStatus.ACTIVE,
        )
        with self.assertRaises(ValidationError):
            bad.full_clean()

    def test_academic_history_retained(self):
        old = StudentClass.objects.create(
            student=self.student,
            classroom=self.classroom,
            academic_year=self.year,
            status=StudentClassStatus.COMPLETED,
        )
        new_year = AcademicYear.objects.create(
            name="2026/2027",
            start_date="2026-09-01",
            end_date="2027-07-31",
            is_active=True,
        )
        new_class = ClassRoom.objects.create(
            course=self.course,
            academic_year=new_year,
            name="PESKA-B",
            level=2,
            capacity=30,
        )
        StudentClass.objects.create(
            student=self.student,
            classroom=new_class,
            academic_year=new_year,
            status=StudentClassStatus.ACTIVE,
        )
        self.assertEqual(self.student.class_assignments.count(), 2)
        self.assertEqual(
            self.student.class_assignments.filter(
                status=StudentClassStatus.COMPLETED
            ).first(),
            old,
        )
