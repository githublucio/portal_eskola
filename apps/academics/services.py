from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.roles import STUDENT, TEACHER
from apps.courses.models import Subject
from apps.students.models import ClassRoom, StudentClass, StudentClassStatus
from apps.teachers.models import Teacher

from .models import (
    AttendanceRecord,
    AttendanceStatus,
    Certificate,
    GradeEntry,
    Notification,
    TimetableSlot,
)


def classrooms_for_teacher(teacher: Teacher):
    teaching_ids = TimetableSlot.objects.filter(
        teacher=teacher, is_active=True
    ).values_list("classroom_id", flat=True)
    return (
        ClassRoom.objects.filter(
            Q(adviser=teacher, is_active=True) | Q(pk__in=teaching_ids)
        )
        .select_related("course", "academic_year")
        .distinct()
        .order_by("name")
    )


def teacher_can_access_classroom(teacher: Teacher, classroom: ClassRoom) -> bool:
    return classrooms_for_teacher(teacher).filter(pk=classroom.pk).exists()


def subjects_for_teacher_classroom(teacher: Teacher, classroom: ClassRoom):
    if classroom.adviser_id == teacher.pk:
        return Subject.objects.filter(course=classroom.course, is_active=True)
    return Subject.objects.filter(
        pk__in=TimetableSlot.objects.filter(
            teacher=teacher, classroom=classroom, is_active=True
        ).values("subject_id")
    )


def active_students_for_classroom(classroom: ClassRoom):
    return (
        StudentClass.objects.filter(
            classroom=classroom, status=StudentClassStatus.ACTIVE
        )
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )


def save_attendance_roster(*, classroom, subject, date, teacher, statuses: dict):
    """statuses: {student_id: status_value}"""
    saved = 0
    for assignment in active_students_for_classroom(classroom):
        student = assignment.student
        status = statuses.get(str(student.pk)) or statuses.get(student.pk)
        if status not in AttendanceStatus.values:
            status = AttendanceStatus.PRESENT
        AttendanceRecord.objects.update_or_create(
            student=student,
            classroom=classroom,
            subject=subject,
            date=date,
            defaults={"status": status, "recorded_by": teacher},
        )
        saved += 1
    return saved


def save_grade_roster(
    *,
    classroom,
    subject,
    academic_year,
    term,
    assessment_name,
    teacher,
    scores: dict,
    max_score,
):
    """scores: {student_id: score_str} — empty values are skipped."""
    saved = 0
    for assignment in active_students_for_classroom(classroom):
        student = assignment.student
        raw = scores.get(str(student.pk)) or scores.get(student.pk)
        if raw in (None, ""):
            continue
        try:
            score = float(raw)
        except (TypeError, ValueError):
            continue
        lookup = {
            "student": student,
            "subject": subject,
            "classroom": classroom,
            "academic_year": academic_year,
            "term": term,
            "assessment_name": assessment_name or "",
        }
        existing = GradeEntry.objects.filter(**lookup).first()
        if existing:
            existing.score = score
            existing.max_score = max_score
            existing.recorded_by = teacher
            existing.save()
        else:
            GradeEntry.objects.create(
                **lookup,
                score=score,
                max_score=max_score,
                recorded_by=teacher,
            )
        saved += 1
    return saved


def next_certificate_number() -> str:
    year = timezone.localdate().year
    prefix = f"CERT-{year}-"
    last = (
        Certificate.objects.filter(certificate_number__startswith=prefix)
        .order_by("-certificate_number")
        .first()
    )
    seq = 1
    if last:
        try:
            seq = int(last.certificate_number.rsplit("-", 1)[-1]) + 1
        except ValueError:
            seq = Certificate.objects.filter(
                certificate_number__startswith=prefix
            ).count() + 1
    return f"{prefix}{seq:04d}"


def users_for_notification_audience(audience: str):
    qs = User.objects.filter(is_active=True)
    if audience == "students":
        return qs.filter(groups__name=STUDENT).distinct()
    if audience == "teachers":
        return qs.filter(groups__name=TEACHER).distinct()
    if audience == "staff":
        return qs.filter(Q(is_staff=True) | Q(is_superuser=True)).distinct()
    return qs


def send_notifications(*, title, message, link, audience, created_by=None):
    users = list(users_for_notification_audience(audience))
    notifications = [
        Notification(user=user, title=title, message=message, link=link or "")
        for user in users
    ]
    Notification.objects.bulk_create(notifications)
    return len(notifications)
