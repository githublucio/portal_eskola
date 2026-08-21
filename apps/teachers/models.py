from django.conf import settings
from django.db import models

from apps.core.validators import validate_image_file
from apps.courses.models import Department


class TeacherStatus(models.TextChoices):
    ACTIVE = "active", "Ativu"
    INACTIVE = "inactive", "Inativu"
    ON_LEAVE = "on_leave", "Lisensa"


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teacher_profile",
    )
    employee_number = models.CharField(max_length=40, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="teachers",
    )
    specialization = models.CharField(max_length=200, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(
        upload_to="teachers/",
        blank=True,
        null=True,
        validators=validate_image_file,
    )
    status = models.CharField(
        max_length=20,
        choices=TeacherStatus.choices,
        default=TeacherStatus.ACTIVE,
        db_index=True,
    )
    hire_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.last_name}, {self.first_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        self.employee_number = (self.employee_number or "").strip().upper()
        super().save(*args, **kwargs)
