from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.core.models import School

from .models import Document, DocumentCategory, PublishStatus


class DocumentPublicTests(TestCase):
    def setUp(self):
        School.get_solo()
        user = get_user_model().objects.create_user("editor", password="pass12345")
        self.category = DocumentCategory.objects.create(name="Formulários", slug="formularios")
        pdf = SimpleUploadedFile("aviso.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        self.public_doc = Document.objects.create(
            title="Formulário inscrição",
            slug="formulario-inscricao",
            category=self.category,
            description="Formulário público",
            file=pdf,
            is_public=True,
            status=PublishStatus.PUBLISHED,
            uploaded_by=user,
        )
        private_pdf = SimpleUploadedFile(
            "interno.pdf", b"%PDF-1.4 private", content_type="application/pdf"
        )
        self.private_doc = Document.objects.create(
            title="Documento interno",
            slug="documento-interno",
            category=self.category,
            file=private_pdf,
            is_public=False,
            status=PublishStatus.PUBLISHED,
            uploaded_by=user,
        )

    def test_list_shows_public_only(self):
        response = self.client.get(reverse("documents:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Formulário inscrição")
        self.assertNotContains(response, "Documento interno")

    def test_public_download(self):
        response = self.client.get(self.public_doc.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertTrue(response["Content-Disposition"].endswith('.pdf"') or "pdf" in response["Content-Disposition"].lower())

    def test_private_download_forbidden(self):
        response = self.client.get(self.private_doc.get_absolute_url())
        self.assertEqual(response.status_code, 404)
