from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.core.models import School
from apps.courses.models import Course, Department, PublishStatus as CourseStatus
from apps.documents.models import Document, DocumentCategory, PublishStatus as DocStatus
from apps.events.models import Event, PublishStatus as EventStatus
from apps.news.models import News, NewsCategory, PublishStatus as NewsStatus

User = get_user_model()


class ApiV1Tests(APITestCase):
    def setUp(self):
        School.get_solo()
        self.category = NewsCategory.objects.create(name="Geral", slug="geral")
        self.published_news = News.objects.create(
            title="Notícia pública",
            slug="noticia-publica",
            category=self.category,
            summary="Resumo",
            content="Conteúdo",
            status=NewsStatus.PUBLISHED,
        )
        News.objects.create(
            title="Rascunho",
            slug="rascunho",
            category=self.category,
            content="Draft",
            status=NewsStatus.DRAFT,
        )
        Event.objects.create(
            title="Dia aberto",
            slug="dia-aberto",
            description="Evento",
            start_at=timezone.now() + timedelta(days=2),
            status=EventStatus.PUBLISHED,
        )
        dept = Department.objects.create(code="PES", name="Peska")
        Course.objects.create(
            department=dept,
            code="PESKA",
            name="Técnico de Peska",
            slug="tecnico-peska",
            status=CourseStatus.PUBLISHED,
        )
        Course.objects.create(
            department=dept,
            code="DRAFT",
            name="Draft course",
            slug="draft-course",
            status=CourseStatus.DRAFT,
        )
        doc_cat = DocumentCategory.objects.create(name="Avisos", slug="avisos")
        Document.objects.create(
            title="Aviso público",
            slug="aviso-publico",
            category=doc_cat,
            file=SimpleUploadedFile("aviso.pdf", b"%PDF-1.4", content_type="application/pdf"),
            is_public=True,
            status=DocStatus.PUBLISHED,
        )
        Document.objects.create(
            title="Interno",
            slug="interno",
            category=doc_cat,
            file=SimpleUploadedFile("interno.pdf", b"%PDF-1.4", content_type="application/pdf"),
            is_public=False,
            status=DocStatus.PUBLISHED,
        )

        self.editor = User.objects.create_user(
            username="api_editor",
            password="complex-pass-123",
            is_staff=True,
        )
        for codename in ("add_news", "change_news", "view_news", "delete_news"):
            self.editor.user_permissions.add(
                Permission.objects.get(codename=codename)
            )
        self.token = Token.objects.create(user=self.editor)

    def test_api_root(self):
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("news", response.data["endpoints"])

    def test_public_news_list_hides_draft(self):
        response = self.client.get("/api/v1/news/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item["title"] for item in response.data["results"]]
        self.assertIn("Notícia pública", titles)
        self.assertNotIn("Rascunho", titles)

    def test_public_courses_and_documents(self):
        courses = self.client.get("/api/v1/courses/")
        self.assertEqual(courses.status_code, status.HTTP_200_OK)
        codes = [item["code"] for item in courses.data["results"]]
        self.assertIn("PESKA", codes)
        self.assertNotIn("DRAFT", codes)

        docs = self.client.get("/api/v1/documents/")
        titles = [item["title"] for item in docs.data["results"]]
        self.assertIn("Aviso público", titles)
        self.assertNotIn("Interno", titles)

    def test_token_auth_and_me(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": "api_editor", "password": "complex-pass-123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        me = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["username"], "api_editor")

    def test_create_news_requires_auth(self):
        response = self.client.post(
            "/api/v1/news/",
            {
                "title": "Nova",
                "category_id": self.category.pk,
                "content": "Texto",
                "status": NewsStatus.DRAFT,
            },
            format="json",
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_staff_can_create_news_with_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(
            "/api/v1/news/",
            {
                "title": "Nova API",
                "category_id": self.category.pk,
                "content": "Criado via API",
                "status": NewsStatus.PUBLISHED,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Nova API")
        self.assertTrue(
            News.objects.filter(title="Nova API", author=self.editor).exists()
        )

    def test_staff_can_list_all_with_flag(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get("/api/v1/news/?all=1")
        titles = [item["title"] for item in response.data["results"]]
        self.assertIn("Rascunho", titles)

    def test_news_detail_by_slug(self):
        response = self.client.get("/api/v1/news/noticia-publica/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["slug"], "noticia-publica")
