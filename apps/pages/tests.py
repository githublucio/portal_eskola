from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core.models import School

from .models import Page, PublishStatus


class PagePublicTests(TestCase):
    def setUp(self):
        School.get_solo()
        user = get_user_model().objects.create_user("editor", password="pass12345")
        self.published = Page.objects.create(
            title="Regulamento",
            slug="regulamento",
            content="Konteúdu regulamento.",
            status=PublishStatus.PUBLISHED,
            author=user,
        )
        self.draft = Page.objects.create(
            title="Rascunho",
            slug="rascunho",
            content="Seidauk publiku.",
            status=PublishStatus.DRAFT,
            author=user,
        )

    def test_published_page_detail(self):
        response = self.client.get(self.published.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Regulamento")

    def test_draft_page_not_public(self):
        response = self.client.get(self.draft.get_absolute_url())
        self.assertEqual(response.status_code, 404)
