from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.core.models import School
from apps.core.validators import FileExtensionValidator, FileSizeValidator
from apps.news.models import News, NewsCategory, PublishStatus

User = get_user_model()


class ValidatorTests(TestCase):
    def test_reject_bad_extension(self):
        validator = FileExtensionValidator(["pdf"])
        bad = SimpleUploadedFile("note.exe", b"x")
        with self.assertRaises(ValidationError):
            validator(bad)

    def test_reject_oversized_file(self):
        validator = FileSizeValidator(1)  # 1 MB
        big = SimpleUploadedFile("big.pdf", b"x" * (1024 * 1024 + 10))
        with self.assertRaises(ValidationError):
            validator(big)


class SecurityBehaviorTests(TestCase):
    def setUp(self):
        School.get_solo()
        self.category = NewsCategory.objects.create(name="Geral", slug="geral")
        News.objects.create(
            title='Test <script>alert("xss")</script>',
            slug="xss-test",
            category=self.category,
            content="Safe body",
            status=PublishStatus.PUBLISHED,
        )

    def test_csrf_required_on_contact(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("contact:contact"),
            {
                "name": "Ana",
                "email": "ana@example.com",
                "subject": "Olá",
                "message": "Mensagem",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_xss_escaped_in_news_list(self):
        response = self.client.get(reverse("news:list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<script>alert")
        self.assertContains(response, "&lt;script&gt;")

    def test_student_pii_absent_from_public_home(self):
        from apps.students.models import Student

        Student.objects.create(
            student_number="S-777",
            first_name="Segredo",
            last_name="Privado",
            email="privado@example.com",
            phone="7777777",
        )
        response = self.client.get(reverse("core:home"))
        self.assertNotContains(response, "Segredo")
        self.assertNotContains(response, "privado@example.com")
        self.assertNotContains(response, "7777777")

    @override_settings(DEBUG=False)
    def test_custom_404_page(self):
        response = self.client.get("/this-page-does-not-exist-xyz/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "errors/404.html")


class ReportsPermissionTests(TestCase):
    def setUp(self):
        School.get_solo()
        self.password = "complex-pass-123"
        self.user = User.objects.create_user(
            username="reportuser",
            password=self.password,
            is_staff=True,
        )

    def test_csv_forbidden_without_perm(self):
        self.client.login(username="reportuser", password=self.password)
        response = self.client.get(reverse("accounts:report_students_csv"))
        self.assertEqual(response.status_code, 403)

    def test_csv_ok_for_superuser(self):
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username="reportuser", password=self.password)
        response = self.client.get(reverse("accounts:report_students_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("student_number", response.content.decode("utf-8"))
