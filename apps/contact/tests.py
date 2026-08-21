from django.test import TestCase
from django.urls import reverse

from apps.core.models import School

from .models import ContactMessage


class ContactPageTests(TestCase):
    def setUp(self):
        School.get_solo()

    def test_contact_page_returns_200(self):
        response = self.client.get(reverse("contact:contact"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "contact/contact.html")

    def test_contact_form_creates_message(self):
        payload = {
            "name": "Maria Silva",
            "email": "maria@example.com",
            "phone": "77000000",
            "subject": "Informasaun kursu",
            "message": "Hakarak hatene kona-ba kursu tekniku.",
        }
        response = self.client.post(reverse("contact:contact"), payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)
        msg = ContactMessage.objects.get()
        self.assertEqual(msg.email, "maria@example.com")
        self.assertFalse(msg.is_read)

    def test_contact_form_requires_fields(self):
        response = self.client.post(reverse("contact:contact"), {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)
