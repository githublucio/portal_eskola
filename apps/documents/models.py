from pathlib import Path

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from apps.core.validators import validate_document_file


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Raskunhu"
    PUBLISHED = "published", "Publika"
    ARCHIVED = "archived", "Arkivu"


class DocumentCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "document category"
        verbose_name_plural = "document categories"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:140] or "category"
        super().save(*args, **kwargs)


class Document(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name="documents",
    )
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="documents/%Y/%m/", validators=validate_document_file)
    version = models.CharField(max_length=40, default="1.0")
    is_public = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
        db_index=True,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    published_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        permissions = [("publish_document", "Can publish document")]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "document"
            slug = base
            counter = 1
            while Document.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.status == PublishStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("documents:download", kwargs={"slug": self.slug})

    @property
    def is_publicly_available(self) -> bool:
        return self.is_public and self.status == PublishStatus.PUBLISHED

    @property
    def file_name(self) -> str:
        if not self.file:
            return ""
        return Path(self.file.name).name

    @property
    def file_extension(self) -> str:
        name = self.file_name
        if "." not in name:
            return ""
        return name.rsplit(".", 1)[-1].lower()

    @property
    def file_icon_class(self) -> str:
        ext = self.file_extension
        mapping = {
            "pdf": "bi-file-earmark-pdf-fill",
            "doc": "bi-file-earmark-word-fill",
            "docx": "bi-file-earmark-word-fill",
            "xls": "bi-file-earmark-excel-fill",
            "xlsx": "bi-file-earmark-excel-fill",
            "ppt": "bi-file-earmark-ppt-fill",
            "pptx": "bi-file-earmark-ppt-fill",
            "zip": "bi-file-earmark-zip-fill",
        }
        return mapping.get(ext, "bi-file-earmark-text-fill")
