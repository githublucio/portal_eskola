from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.core.models import School

from .models import AcademicYear, Course, Department, PublishStatus, Subject


class CoursePublicTests(TestCase):
    def setUp(self):
        School.get_solo()
        self.dept = Department.objects.create(code="INF", name="Informática")
        self.published = Course.objects.create(
            department=self.dept,
            code="TI",
            name="Técnico de Informática",
            slug="tecnico-informatica",
            description="Curso de informática",
            qualification="Certificado Técnico",
            status=PublishStatus.PUBLISHED,
        )
        Subject.objects.create(
            course=self.published,
            code="PROG1",
            name="Programação I",
            semester=1,
            credits=4,
        )
        Course.objects.create(
            department=self.dept,
            code="DRAFT",
            name="Curso Draft",
            slug="curso-draft",
            status=PublishStatus.DRAFT,
        )

    def test_list_published_only(self):
        response = self.client.get(reverse("courses:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Técnico de Informática")
        self.assertNotContains(response, "Curso Draft")

    def test_detail_shows_subjects(self):
        response = self.client.get(self.published.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Programação I")
        self.assertContains(response, "PROG1")

    def test_filter_by_department(self):
        other = Department.objects.create(code="MEC", name="Mecânica")
        Course.objects.create(
            department=other,
            code="MEC1",
            name="Mecânica Geral",
            slug="mecanica-geral",
            status=PublishStatus.PUBLISHED,
        )
        response = self.client.get(reverse("courses:list"), {"department": "INF"})
        self.assertContains(response, "Técnico de Informática")
        self.assertNotContains(response, "Mecânica Geral")


class AcademicYearTests(TestCase):
    def test_only_one_active_year(self):
        y1 = AcademicYear.objects.create(
            name="2024/2025",
            start_date="2024-09-01",
            end_date="2025-07-31",
            is_active=True,
        )
        y2 = AcademicYear.objects.create(
            name="2025/2026",
            start_date="2025-09-01",
            end_date="2026-07-31",
            is_active=True,
        )
        y1.refresh_from_db()
        y2.refresh_from_db()
        self.assertFalse(y1.is_active)
        self.assertTrue(y2.is_active)

    def test_end_before_start_invalid(self):
        year = AcademicYear(
            name="Bad",
            start_date="2026-09-01",
            end_date="2026-01-01",
        )
        with self.assertRaises(ValidationError):
            year.full_clean()
