from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.core.models import School

from .models import GalleryAlbum, GalleryPhoto, PublishStatus


def tiny_gif():
    return SimpleUploadedFile(
        "photo.gif",
        (
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
            b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
            b"\x00\x02\x02D\x01\x00;"
        ),
        content_type="image/gif",
    )


class GalleryPublicTests(TestCase):
    def setUp(self):
        School.get_solo()
        self.album = GalleryAlbum.objects.create(
            title="Dia aberto",
            slug="dia-aberto",
            description="Fotos do dia aberto",
            status=PublishStatus.PUBLISHED,
            cover_image=tiny_gif(),
        )
        GalleryPhoto.objects.create(
            album=self.album,
            image=tiny_gif(),
            caption="Entrada",
            sort_order=1,
        )
        GalleryAlbum.objects.create(
            title="Draft album",
            slug="draft-album",
            status=PublishStatus.DRAFT,
        )

    def test_list_published_only(self):
        response = self.client.get(reverse("gallery:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dia aberto")
        self.assertNotContains(response, "Draft album")

    def test_detail_shows_photos(self):
        response = self.client.get(self.album.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entrada")

    def test_detail_shows_cover_when_no_photos(self):
        empty = GalleryAlbum.objects.create(
            title="Kapa de'it",
            slug="kapa-deit",
            status=PublishStatus.PUBLISHED,
            cover_image=tiny_gif(),
        )
        response = self.client.get(empty.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, empty.cover_image.url)
        self.assertNotContains(response, "seidauk iha foto")

    def test_ensure_cover_photo_creates_first_photo(self):
        album = GalleryAlbum.objects.create(
            title="Sinc cover",
            slug="sinc-cover",
            status=PublishStatus.PUBLISHED,
            cover_image=tiny_gif(),
        )
        self.assertEqual(album.photos.count(), 0)
        created = album.ensure_cover_photo()
        self.assertIsNotNone(created)
        self.assertEqual(album.photos.count(), 1)
        self.assertEqual(album.photos.first().image.name, album.cover_image.name)
        self.assertIsNone(album.ensure_cover_photo())
