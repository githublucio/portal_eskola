from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Raskunhu"
    PUBLISHED = "published", "Publika"
    ARCHIVED = "archived", "Arkivu"


class NewsCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "news category"
        verbose_name_plural = "news categories"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:140] or "category"
        super().save(*args, **kwargs)


class News(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    category = models.ForeignKey(
        NewsCategory,
        on_delete=models.PROTECT,
        related_name="news_items",
    )
    summary = models.CharField(max_length=300, blank=True)
    content = models.TextField()
    featured_image = models.ImageField(upload_to="news/", blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
        db_index=True,
    )
    is_announcement = models.BooleanField(
        default=False,
        help_text="Hatudu hanesan avisu importante iha pájina inísiu.",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news_items",
    )
    published_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "news"
        verbose_name_plural = "news"
        permissions = [
            ("publish_news", "Can publish news"),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "news"
            slug = base
            counter = 1
            while News.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.status == PublishStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("news:detail", kwargs={"slug": self.slug})
