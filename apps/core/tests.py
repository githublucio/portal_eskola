from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.gallery.models import GalleryAlbum, GalleryPhoto
from apps.gallery.models import PublishStatus as GalleryStatus

from .models import School


def tiny_gif(name="photo.gif"):
    return SimpleUploadedFile(
        name,
        (
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
            b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
            b"\x00\x02\x02D\x01\x00;"
        ),
        content_type="image/gif",
    )


class SchoolModelTests(TestCase):
    def test_get_solo_creates_default_profile(self):
        school = School.get_solo()
        self.assertEqual(school.pk, 1)
        self.assertIn("Atauro", school.name)

    def test_save_keeps_singleton_pk(self):
        school = School.get_solo()
        school.name = "ETVP Atauro Updated"
        school.save()
        self.assertEqual(School.objects.count(), 1)
        self.assertEqual(School.objects.get(pk=1).name, "ETVP Atauro Updated")


class PublicPageTests(TestCase):
    def setUp(self):
        self.school = School.get_solo()

    def test_home_returns_200(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.school.name)
        self.assertContains(response, "Kona-ba Ami")
        self.assertContains(response, "Ajenda eskola")
        self.assertTemplateUsed(response, "core/home.html")
        self.assertTemplateUsed(response, "base.html")

    def test_map_embed_uses_address_or_coordinates(self):
        self.school.address = "Vila, Atauro, Timor-Leste"
        self.school.map_latitude = None
        self.school.map_longitude = None
        self.school.save()
        self.assertIn("output=embed", self.school.map_embed_src)
        self.assertIn("Atauro", self.school.map_embed_src)
        self.school.map_latitude = "-8.266700"
        self.school.map_longitude = "125.608300"
        self.school.save()
        self.assertIn("-8.266700", self.school.map_embed_src)

    def test_about_returns_200(self):
        response = self.client.get(reverse("core:about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kona-ba eskola")
        self.assertTemplateUsed(response, "core/about.html")

    def test_hero_uses_logo_from_settings(self):
        self.school.logo = tiny_gif("logo-eskola.gif")
        self.school.save()
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, self.school.logo.url)

    def test_hero_slider_uses_gallery_photos(self):
        album = GalleryAlbum.objects.create(
            title="Loron eskola",
            slug="loron-eskola",
            status=GalleryStatus.PUBLISHED,
        )
        GalleryPhoto.objects.create(
            album=album,
            image=tiny_gif("slide.gif"),
            caption="Kampus Atauro",
        )
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "heroCarousel")
        self.assertContains(response, "Kampus Atauro")
        self.assertContains(response, reverse("gallery:list"))

    def test_nav_links_present(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, reverse("core:about"))
        self.assertContains(response, reverse("contact:contact"))
        self.assertContains(response, "Kona-ba Ami")
        self.assertContains(response, "Kontaktu")
