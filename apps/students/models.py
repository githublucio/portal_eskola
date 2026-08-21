from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.validators import validate_image_file
from apps.courses.models import AcademicYear, Course
from apps.teachers.models import Teacher


class StudentStatus(models.TextChoices):
    ACTIVE = "active", "Ativu"
    INACTIVE = "inactive", "Inativu"
    GRADUATED = "graduated", "Graduadu"
    TRANSFERRED = "transferred", "Transfere"
    SUSPENDED = "suspended", "Suspende"


class Gender(models.TextChoices):
    MALE = "M", "Mane"
    FEMALE = "F", "Feto"
    OTHER = "O", "Seluk"


class EnrollmentStatus(models.TextChoices):
    PENDING = "pending", "Hein"
    ACTIVE = "active", "Ativu"
    COMPLETED = "completed", "Remata"
    WITHDRAWN = "withdrawn", "Desiste"
    TRANSFERRED = "transferred", "Transfere"


class StudentClassStatus(models.TextChoices):
    ACTIVE = "active", "Ativu"
    COMPLETED = "completed", "Remata"
    TRANSFERRED = "transferred", "Transfere"
    DROPPED = "dropped", "Sai"


class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
    )
    student_number = models.CharField(max_length=40, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    address = models.CharField(max_length=255, blank=True)
    guardian_name = models.CharField(max_length=150, blank=True)
    guardian_phone = models.CharField(max_length=40, blank=True)
    photo = models.ImageField(
        upload_to="students/",
        blank=True,
        null=True,
        validators=validate_image_file,
    )
    status = models.CharField(
        max_length=20,
        choices=StudentStatus.choices,
        default=StudentStatus.ACTIVE,
        db_index=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.student_number} — {self.full_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        self.student_number = (self.student_number or "").strip().upper()
        super().save(*args, **kwargs)

    def current_enrollment(self):
        return (
            self.enrollments.filter(status=EnrollmentStatus.ACTIVE)
            .select_related("course", "academic_year")
            .first()
        )

    def current_class(self):
        return (
            self.class_assignments.filter(status=StudentClassStatus.ACTIVE)
            .select_related("classroom", "academic_year")
            .first()
        )


class Enrollment(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    enrollment_number = models.CharField(max_length=50, unique=True)
    enrollment_date = models.DateField(default=timezone.localdate)
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
        db_index=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-enrollment_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course", "academic_year"],
                name="uniq_enrollment_student_course_year",
            ),
        ]
        verbose_name = "enrollment"
        verbose_name_plural = "enrollments"

    def __str__(self) -> str:
        return f"{self.enrollment_number} — {self.student}"

    def clean(self):
        if (
            self.status == EnrollmentStatus.ACTIVE
            and self.student_id
            and Enrollment.objects.filter(
                student_id=self.student_id,
                status=EnrollmentStatus.ACTIVE,
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                {
                    "status": (
                        "Estudante ja iha enrollment ativu. "
                        "Remata enrollment uluk molok ativa ida foun."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.enrollment_number = (self.enrollment_number or "").strip().upper()
        if not self.enrollment_number:
            year_label = ""
            if self.academic_year_id:
                year_label = self.academic_year.name.replace("/", "")[:8]
            base = f"ENR-{year_label}-{self.student.student_number}"
            number = base
            counter = 1
            while Enrollment.objects.exclude(pk=self.pk).filter(
                enrollment_number=number
            ).exists():
                number = f"{base}-{counter}"
                counter += 1
            self.enrollment_number = number
        super().save(*args, **kwargs)


class ClassRoom(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="classrooms",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="classrooms",
    )
    name = models.CharField(max_length=80, help_text="Ez: TI-A, TVP-A")
    level = models.PositiveSmallIntegerField(default=1, help_text="Nível / tinan")
    capacity = models.PositiveIntegerField(default=30)
    adviser = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="advised_classes",
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["academic_year", "course", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "academic_year", "name"],
                name="uniq_classroom_course_year_name",
            ),
        ]
        verbose_name = "class room"
        verbose_name_plural = "class rooms"

    def __str__(self) -> str:
        return f"{self.name} ({self.academic_year})"

    @property
    def enrolled_count(self) -> int:
        return self.student_assignments.filter(
            status=StudentClassStatus.ACTIVE
        ).count()

    def clean(self):
        if self.capacity is not None and self.capacity < 1:
            raise ValidationError({"capacity": "Kapasidade tenke mínimu 1."})


class StudentClass(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="class_assignments",
    )
    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.PROTECT,
        related_name="student_assignments",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="student_classes",
    )
    status = models.CharField(
        max_length=20,
        choices=StudentClassStatus.choices,
        default=StudentClassStatus.ACTIVE,
        db_index=True,
    )
    assigned_at = models.DateField(default=timezone.localdate)
    left_at = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-academic_year__start_date", "student__last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "classroom", "academic_year"],
                name="uniq_student_class_assignment",
            ),
        ]
        verbose_name = "student class"
        verbose_name_plural = "student classes"

    def __str__(self) -> str:
        return f"{self.student} → {self.classroom}"

    def clean(self):
        if self.classroom_id and self.academic_year_id:
            if self.classroom.academic_year_id != self.academic_year_id:
                raise ValidationError(
                    {
                        "academic_year": (
                            "Tinan akadémiku tenke hanesan ho turma."
                        )
                    }
                )
        if (
            self.status == StudentClassStatus.ACTIVE
            and self.student_id
            and StudentClass.objects.filter(
                student_id=self.student_id,
                status=StudentClassStatus.ACTIVE,
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                {
                    "status": (
                        "Estudante ja iha turma ativa. "
                        "Remata atribuisaun uluk molok."
                    )
                }
            )
        if (
            self.status == StudentClassStatus.ACTIVE
            and self.classroom_id
            and self.classroom.capacity
        ):
            active = (
                StudentClass.objects.filter(
                    classroom_id=self.classroom_id,
                    status=StudentClassStatus.ACTIVE,
                )
                .exclude(pk=self.pk)
                .count()
            )
            if active >= self.classroom.capacity:
                raise ValidationError(
                    {"classroom": "Turma kompleta (kapasidade máximu)."}
                )

    def save(self, *args, **kwargs):
        if self.classroom_id and not self.academic_year_id:
            self.academic_year = self.classroom.academic_year
        if (
            self.status != StudentClassStatus.ACTIVE
            and self.left_at is None
            and self.pk
        ):
            self.left_at = timezone.localdate()
        super().save(*args, **kwargs)
