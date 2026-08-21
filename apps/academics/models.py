from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.validators import validate_application_attachment
from apps.courses.models import AcademicYear, Subject
from apps.students.models import ClassRoom, Student
from apps.teachers.models import Teacher


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Iha"
    ABSENT = "absent", "Falta"
    LATE = "late", "Tardi"
    EXCUSED = "excused", "Justifika"


class Weekday(models.IntegerChoices):
    MONDAY = 1, "Segunda"
    TUESDAY = 2, "Tersa"
    WEDNESDAY = 3, "Kuarta"
    THURSDAY = 4, "Kinta"
    FRIDAY = 5, "Sesta"
    SATURDAY = 6, "Sábadu"


class ApplicationStatus(models.TextChoices):
    NEW = "new", "Foun"
    REVIEWING = "reviewing", "Analiza"
    ACCEPTED = "accepted", "Simu"
    REJECTED = "rejected", "Rejeita"
    WAITLIST = "waitlist", "Lista hein"


class CertificateStatus(models.TextChoices):
    DRAFT = "draft", "Raskunhu"
    ISSUED = "issued", "Emite"
    REVOKED = "revoked", "Revoga"


class AttendanceRecord(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="attendance_records"
    )
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name="attendance_records"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )
    date = models.DateField(default=timezone.localdate, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
    )
    recorded_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_marked",
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "student__last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "classroom", "date", "subject"],
                name="uniq_attendance_student_class_date_subject",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.student} · {self.date} · {self.status}"


class GradeEntry(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="grades"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name="grades"
    )
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.PROTECT, related_name="grades"
    )
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.PROTECT, related_name="grades"
    )
    term = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="Períodu (1–4)",
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100,
        validators=[MinValueValidator(1)],
    )
    assessment_name = models.CharField(max_length=120, blank=True)
    recorded_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grades_recorded",
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-academic_year__start_date", "subject__code", "term"]
        verbose_name = "grade"
        verbose_name_plural = "grades"

    def __str__(self) -> str:
        return f"{self.student} · {self.subject} · {self.score}"

    @property
    def percentage(self) -> float:
        if not self.max_score:
            return 0.0
        return float(self.score) * 100.0 / float(self.max_score)

    def clean(self):
        if self.score is not None and self.max_score is not None:
            if self.score > self.max_score:
                raise ValidationError({"score": "Nota la bele boot liu máximum."})
        if self.classroom_id and self.academic_year_id:
            if self.classroom.academic_year_id != self.academic_year_id:
                raise ValidationError(
                    {"academic_year": "Tinan akadémiku tenke hanesan ho turma."}
                )


class TimetableSlot(models.Model):
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name="timetable_slots"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name="timetable_slots"
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timetable_slots",
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["weekday", "start_time"]
        verbose_name = "timetable slot"
        verbose_name_plural = "timetable slots"

    def __str__(self) -> str:
        return f"{self.get_weekday_display()} {self.start_time}-{self.end_time} · {self.subject}"

    def clean(self):
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "Oras remata tenke liu oras hahú."})


class Certificate(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="certificates"
    )
    title = models.CharField(max_length=200)
    certificate_number = models.CharField(max_length=60, unique=True)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
    )
    issued_at = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=CertificateStatus.choices,
        default=CertificateStatus.DRAFT,
    )
    notes = models.TextField(blank=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates_issued",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issued_at", "-created_at"]

    def __str__(self) -> str:
        return f"{self.certificate_number} — {self.title}"

    def save(self, *args, **kwargs):
        self.certificate_number = (self.certificate_number or "").strip().upper()
        if self.status == CertificateStatus.ISSUED and self.issued_at is None:
            self.issued_at = timezone.localdate()
        super().save(*args, **kwargs)


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user}: {self.title}"


class OnlineApplication(models.Model):
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    desired_course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    desired_course_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="Se kursu seidauk iha lista",
    )
    previous_school = models.CharField(max_length=200, blank=True)
    motivation = models.TextField(blank=True)
    certificate_file = models.FileField(
        upload_to="applications/certificates/",
        blank=True,
        null=True,
        validators=validate_application_attachment,
        help_text="Sertifikadu Pre-Sekundária (PDF/JPG/PNG, máximu 2MB)",
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.NEW,
        db_index=True,
    )
    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "online application"
        verbose_name_plural = "online applications"

    def __str__(self) -> str:
        return f"{self.full_name} ({self.get_status_display()})"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        born = self.date_of_birth
        return today.year - born.year - (
            (today.month, today.day) < (born.month, born.day)
        )


class ApplicationSettings(models.Model):
    """Singleton settings for the public online application form."""

    is_open = models.BooleanField(
        default=True,
        help_text="Se desliga, formuláriu kandidatura taka (non-active).",
    )
    title = models.CharField(max_length=200, default="Kandidatura online")
    intro = models.TextField(
        blank=True,
        default=(
            "Preenxe formuláriu. Ekipa eskola sei analiza no kontakta ita "
            "liuhusi korreiu ka telefone."
        ),
    )
    closed_message = models.TextField(
        blank=True,
        default=(
            "Kandidatura online taka ona. Favor kontakta eskola ba informasaun "
            "tanba tinan letivu oin mai."
        ),
    )
    min_age = models.PositiveSmallIntegerField(default=15)
    max_age = models.PositiveSmallIntegerField(default=21)
    opens_at = models.DateTimeField(blank=True, null=True)
    closes_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "application settings"
        verbose_name_plural = "application settings"

    def __str__(self) -> str:
        return "Konfigurasaun kandidatura"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls) -> "ApplicationSettings":
        obj, created = cls.objects.get_or_create(pk=1)
        if created:
            ApplicationCriterion.ensure_defaults()
        return obj

    @property
    def is_accepting(self) -> bool:
        if not self.is_open:
            return False
        now = timezone.now()
        if self.opens_at and now < self.opens_at:
            return False
        if self.closes_at and now > self.closes_at:
            return False
        return True


class ApplicationCriterion(models.Model):
    text = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "application criterion"
        verbose_name_plural = "application criteria"

    def __str__(self) -> str:
        return self.text[:80]

    @classmethod
    def ensure_defaults(cls) -> None:
        if cls.objects.exists():
            return
        defaults = [
            (10, "Idade mínimu 15 tinan no máximu 21 tinan iha tinan letivu ne'e."),
            (
                20,
                "Tenke submete tiha ona dokumentu sertifikadu remata "
                "Eskola Pre-Sekundária (SMP).",
            ),
            (
                30,
                "Preenxe de'it kampu hotu ne'ebé iha sinál asterisku (*).",
            ),
        ]
        cls.objects.bulk_create(
            [cls(sort_order=order, text=text) for order, text in defaults]
        )

