from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import School

from .models import Event, PublishStatus


class EventPublicTests(TestCase):
    def setUp(self):
        School.get_solo()
        user = get_user_model().objects.create_user("editor", password="pass12345")
        now = timezone.now()
        self.upcoming = Event.objects.create(
            title="Feira técnica",
            slug="feira-tecnica",
            description="Evento aberto.",
            location="Campus Atauro",
            start_at=now + timezone.timedelta(days=3),
            status=PublishStatus.PUBLISHED,
            author=user,
        )
        Event.objects.create(
            title="Evento passado",
            slug="evento-passado",
            description="Já aconteceu.",
            start_at=now - timezone.timedelta(days=5),
            status=PublishStatus.PUBLISHED,
            author=user,
        )
        Event.objects.create(
            title="Draft event",
            slug="draft-event",
            description="Draft",
            start_at=now + timezone.timedelta(days=1),
            status=PublishStatus.DRAFT,
            author=user,
        )

    def test_upcoming_list(self):
        response = self.client.get(reverse("events:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Feira técnica")
        self.assertNotContains(response, "Evento passado")
        self.assertNotContains(response, "Draft event")

    def test_past_list(self):
        response = self.client.get(reverse("events:list"), {"scope": "past"})
        self.assertContains(response, "Evento passado")
        self.assertNotContains(response, "Feira técnica")

    def test_detail(self):
        response = self.client.get(self.upcoming.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Campus Atauro")
