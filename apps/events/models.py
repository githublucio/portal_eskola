from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from apps.core.validators import validate_image_file


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Raskunhu"
    PUBLISHED = "published", "Publika"
    ARCHIVED = "archived", "Arkivu"


class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    organizer = models.CharField(max_length=150, blank=True)
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField(blank=True, null=True)
    image = models.ImageField(
        upload_to="events/",
        blank=True,
        null=True,
        validators=validate_image_file,
    )
    status = models.CharField(
        max_length=20,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
        db_index=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at"]
        permissions = [("publish_event", "Can publish event")]

    def __str__(self) -> str:
        return self.title

    def clean(self):
        if self.end_at and self.start_at and self.end_at < self.start_at:
            raise ValidationError({"end_at": "Data/oras remata tenke liu data/oras hahú."})

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "event"
            slug = base
            counter = 1
            while Event.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.status == PublishStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("events:detail", kwargs={"slug": self.slug})

    @property
    def is_upcoming(self) -> bool:
        return self.start_at >= timezone.now()
