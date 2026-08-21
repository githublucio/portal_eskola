from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from apps.core.validators import validate_image_file


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Raskunhu"
    PUBLISHED = "published", "Publika"
    ARCHIVED = "archived", "Arkivu"


class GalleryAlbum(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to="gallery/covers/",
        blank=True,
        null=True,
        validators=validate_image_file,
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="albums",
    )
    status = models.CharField(
        max_length=20,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "gallery album"
        verbose_name_plural = "gallery albums"
        permissions = [("publish_galleryalbum", "Can publish gallery album")]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "album"
            slug = base
            counter = 1
            while GalleryAlbum.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.status == PublishStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("gallery:detail", kwargs={"slug": self.slug})

    def ensure_cover_photo(self):
        """If album has a cover but no photos, add the cover as the first photo.

        Hero slides link to the album page; without photos that page looks empty
        even though a cover image is shown on the home slider.
        """
        if not self.pk or not self.cover_image:
            return None
        if self.photos.exists():
            return None
        photo = GalleryPhoto(album=self, caption=self.title, sort_order=0)
        photo.image.name = self.cover_image.name
        photo.save()
        return photo


class GalleryPhoto(models.Model):
    album = models.ForeignKey(
        GalleryAlbum,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.ImageField(upload_to="gallery/photos/", validators=validate_image_file)
    caption = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "gallery photo"
        verbose_name_plural = "gallery photos"

    def __str__(self) -> str:
        return self.caption or f"Photo {self.pk}"
