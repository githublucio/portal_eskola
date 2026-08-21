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


class Department(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def save(self, *args, **kwargs):
        self.code = (self.code or "").strip().upper()
        super().save(*args, **kwargs)


class AcademicYear(models.Model):
    name = models.CharField(max_length=40, unique=True, help_text="Ez: 2025/2026")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(
        default=False,
        help_text="Tinan akadémiku ida de'it tenke ativu iha tempu ida.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "academic year"
        verbose_name_plural = "academic years"

    def __str__(self) -> str:
        return self.name

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "Data remata tenke liu data hahú."})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            AcademicYear.objects.filter(is_active=True).exclude(pk=self.pk).update(
                is_active=False
            )


class Course(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="courses",
    )
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    duration = models.CharField(
        max_length=80,
        blank=True,
        help_text="Ez: tinan 3, períodu 6",
    )
    qualification = models.CharField(max_length=150, blank=True)
    requirements = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="courses/",
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
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        permissions = [("publish_course", "Can publish course")]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def save(self, *args, **kwargs):
        self.code = (self.code or "").strip().upper()
        if not self.slug:
            base = slugify(self.name)[:200] or slugify(self.code)[:200] or "course"
            slug = base
            counter = 1
            while Course.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.status == PublishStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("courses:detail", kwargs={"slug": self.slug})


class Subject(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="subjects",
    )
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credits = models.PositiveSmallIntegerField(default=0)
    semester = models.PositiveSmallIntegerField(
        default=1,
        help_text="Períodu / nível iha kursu",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course", "semester", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "code"],
                name="uniq_subject_code_per_course",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def save(self, *args, **kwargs):
        self.code = (self.code or "").strip().upper()
        super().save(*args, **kwargs)


def get_active_academic_year():
    return AcademicYear.objects.filter(is_active=True).first()
