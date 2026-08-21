from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core.models import School

from .models import News, NewsCategory, PublishStatus


class NewsPublicTests(TestCase):
    def setUp(self):
        School.get_solo()
        user = get_user_model().objects.create_user("editor", password="pass12345")
        self.category = NewsCategory.objects.create(name="Geral", slug="geral")
        self.other = NewsCategory.objects.create(name="Académico", slug="academico")
        self.published = News.objects.create(
            title="Abertura ano letivo",
            slug="abertura-ano-letivo",
            category=self.category,
            summary="Resumo abertura",
            content="Konteúdu notísia.",
            status=PublishStatus.PUBLISHED,
            is_announcement=True,
            author=user,
        )
        News.objects.create(
            title="Draft item",
            slug="draft-item",
            category=self.category,
            content="Draft",
            status=PublishStatus.DRAFT,
            author=user,
        )
        News.objects.create(
            title="Resultado exame",
            slug="resultado-exame",
            category=self.other,
            content="Exame",
            status=PublishStatus.PUBLISHED,
            author=user,
        )

    def test_news_list_shows_published_only(self):
        response = self.client.get(reverse("news:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Abertura ano letivo")
        self.assertNotContains(response, "Draft item")

    def test_news_detail(self):
        response = self.client.get(self.published.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Konteúdu notísia")

    def test_filter_by_category(self):
        response = self.client.get(reverse("news:list"), {"category": "academico"})
        self.assertContains(response, "Resultado exame")
        self.assertNotContains(response, "Abertura ano letivo")

    def test_search(self):
        response = self.client.get(reverse("news:list"), {"q": "abertura"})
        self.assertContains(response, "Abertura ano letivo")
        self.assertNotContains(response, "Resultado exame")

    def test_home_shows_announcements(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Abertura ano letivo")
