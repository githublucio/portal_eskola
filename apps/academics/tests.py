from datetime import time

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import School
from apps.courses.models import AcademicYear, Course, Department, PublishStatus, Subject
from apps.students.models import ClassRoom, Student, StudentClass, StudentClassStatus
from apps.teachers.models import Teacher

from .models import (
    AttendanceRecord,
    AttendanceStatus,
    Certificate,
    CertificateStatus,
    GradeEntry,
    Notification,
    OnlineApplication,
    ApplicationCriterion,
    ApplicationSettings,
    TimetableSlot,
    Weekday,
)

User = get_user_model()


class AcademicsFixturesMixin:
    def setUp(self):
        School.get_solo()
        self.dept = Department.objects.create(code="PES", name="Peska")
        self.year = AcademicYear.objects.create(
            name="2025/2026",
            start_date="2025-09-01",
            end_date="2026-07-31",
            is_active=True,
        )
        self.course = Course.objects.create(
            department=self.dept,
            code="PESKA",
            name="Técnico de Peska",
            slug="tecnico-peska",
            status=PublishStatus.PUBLISHED,
        )
        self.subject = Subject.objects.create(
            course=self.course, code="BIO1", name="Biologia Marinha", semester=1
        )
        self.teacher_user = User.objects.create_user(
            username="prof1", password="complex-pass-123"
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            employee_number="T-9",
            first_name="Ana",
            last_name="Costa",
            department=self.dept,
        )
        self.student_user = User.objects.create_user(
            username="aluno1", password="complex-pass-123"
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_number="S-900",
            first_name="João",
            last_name="Pereira",
        )
        self.classroom = ClassRoom.objects.create(
            course=self.course,
            academic_year=self.year,
            name="PESKA-A",
            capacity=30,
            adviser=self.teacher,
        )
        StudentClass.objects.create(
            student=self.student,
            classroom=self.classroom,
            academic_year=self.year,
            status=StudentClassStatus.ACTIVE,
        )


class OnlineApplicationTests(TestCase):
    def setUp(self):
        School.get_solo()
        self.settings = ApplicationSettings.get_solo()
        today = timezone.localdate()
        try:
            self.valid_birth = today.replace(year=today.year - 16)
        except ValueError:
            self.valid_birth = today.replace(year=today.year - 16, month=2, day=28)

    def _certificate(self):
        return SimpleUploadedFile(
            "sertifikadu.pdf",
            b"%PDF-1.4 sample certificate",
            content_type="application/pdf",
        )

    def _payload(self, **overrides):
        data = {
            "full_name": "Maria Silva",
            "email": "maria@example.com",
            "phone": "123456",
            "date_of_birth": self.valid_birth.isoformat(),
            "previous_school": "EBS Vila",
            "desired_course_text": "Peska",
            "motivation": "Quero estudar peska",
            "certificate_file": self._certificate(),
        }
        data.update(overrides)
        return data

    def test_apply_page_shows_criteria(self):
        response = self.client.get(reverse("academics:apply"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kritériu ba Kandidatura Online")
        self.assertTrue(ApplicationCriterion.objects.filter(is_active=True).exists())

    def test_apply_page_and_submit(self):
        response = self.client.post(reverse("academics:apply"), self._payload())
        self.assertEqual(response.status_code, 302)
        app = OnlineApplication.objects.get(email="maria@example.com")
        self.assertTrue(app.certificate_file)
        self.assertEqual(app.previous_school, "EBS Vila")

    def test_reject_underage_applicant(self):
        today = timezone.localdate()
        try:
            young = today.replace(year=today.year - 10)
        except ValueError:
            young = today.replace(year=today.year - 10, month=2, day=28)
        response = self.client.post(
            reverse("academics:apply"),
            self._payload(date_of_birth=young.isoformat()),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OnlineApplication.objects.count(), 0)
        self.assertContains(response, "mínimu")

    def test_reject_without_certificate(self):
        payload = self._payload()
        payload.pop("certificate_file")
        response = self.client.post(reverse("academics:apply"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OnlineApplication.objects.count(), 0)

    def test_closed_form_hides_inputs(self):
        self.settings.is_open = False
        self.settings.closed_message = "Pendaftaran remata ona."
        self.settings.save()
        response = self.client.get(reverse("academics:apply"))
        self.assertContains(response, "Pendaftaran remata ona.")
        self.assertNotContains(response, "Haruka kandidatura")
        response = self.client.post(reverse("academics:apply"), self._payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OnlineApplication.objects.count(), 0)


class StudentPortalTests(AcademicsFixturesMixin, TestCase):
    def test_student_portal_requires_link(self):
        User.objects.create_user(username="nolink", password="complex-pass-123")
        self.client.login(username="nolink", password="complex-pass-123")
        response = self.client.get(reverse("academics:student_portal"))
        self.assertEqual(response.status_code, 403)

    def test_student_sees_own_grades(self):
        GradeEntry.objects.create(
            student=self.student,
            subject=self.subject,
            classroom=self.classroom,
            academic_year=self.year,
            term=1,
            score=85,
            recorded_by=self.teacher,
        )
        other = Student.objects.create(
            student_number="S-901", first_name="Outro", last_name="Aluno"
        )
        GradeEntry.objects.create(
            student=other,
            subject=self.subject,
            classroom=self.classroom,
            academic_year=self.year,
            term=1,
            score=41.25,
        )
        self.client.login(username="aluno1", password="complex-pass-123")
        response = self.client.get(reverse("academics:student_grades"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "85")
        self.assertNotContains(response, "41,25")
        self.assertNotContains(response, "41.25")


class TeacherPortalTests(AcademicsFixturesMixin, TestCase):
    def test_teacher_marks_attendance(self):
        self.client.login(username="prof1", password="complex-pass-123")
        date = timezone.localdate().isoformat()
        response = self.client.post(
            reverse("academics:teacher_attendance_mark"),
            {
                "classroom": self.classroom.pk,
                "subject": self.subject.pk,
                "date": date,
                f"status_{self.student.pk}": AttendanceStatus.ABSENT,
            },
        )
        self.assertEqual(response.status_code, 302)
        record = AttendanceRecord.objects.get(
            student=self.student, classroom=self.classroom, subject=self.subject
        )
        self.assertEqual(record.status, AttendanceStatus.ABSENT)
        self.assertEqual(record.recorded_by, self.teacher)

    def test_teacher_enters_grades(self):
        self.client.login(username="prof1", password="complex-pass-123")
        response = self.client.post(
            reverse("academics:teacher_grades_entry"),
            {
                "classroom": self.classroom.pk,
                "subject": self.subject.pk,
                "term": 1,
                "assessment_name": "Teste 1",
                "max_score": "100",
                f"score_{self.student.pk}": "88",
            },
        )
        self.assertEqual(response.status_code, 302)
        grade = GradeEntry.objects.get(student=self.student, assessment_name="Teste 1")
        self.assertEqual(float(grade.score), 88)
        self.assertEqual(grade.recorded_by, self.teacher)

    def test_other_teacher_cannot_mark_foreign_class(self):
        other_user = User.objects.create_user(
            username="prof2", password="complex-pass-123"
        )
        Teacher.objects.create(
            user=other_user,
            employee_number="T-10",
            first_name="Rui",
            last_name="Lopes",
            department=self.dept,
        )
        self.client.login(username="prof2", password="complex-pass-123")
        response = self.client.post(
            reverse("academics:teacher_attendance_mark"),
            {
                "classroom": self.classroom.pk,
                "subject": self.subject.pk,
                "date": timezone.localdate().isoformat(),
                f"status_{self.student.pk}": AttendanceStatus.PRESENT,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_teacher_portal_and_class_list(self):
        TimetableSlot.objects.create(
            classroom=self.classroom,
            subject=self.subject,
            teacher=self.teacher,
            weekday=Weekday.MONDAY,
            start_time=time(8, 0),
            end_time=time(9, 30),
            room="A1",
        )
        self.client.login(username="prof1", password="complex-pass-123")
        home = self.client.get(reverse("academics:teacher_portal"))
        self.assertEqual(home.status_code, 200)
        students = self.client.get(
            reverse("academics:teacher_class_students", args=[self.classroom.pk])
        )
        self.assertEqual(students.status_code, 200)
        self.assertContains(students, "João")


class AcademicsModelTests(AcademicsFixturesMixin, TestCase):
    def test_attendance_and_certificate(self):
        AttendanceRecord.objects.create(
            student=self.student,
            classroom=self.classroom,
            subject=self.subject,
            date=timezone.localdate(),
            status=AttendanceStatus.PRESENT,
            recorded_by=self.teacher,
        )
        cert = Certificate.objects.create(
            student=self.student,
            title="Conclusão",
            certificate_number="cert-1",
            academic_year=self.year,
            status=CertificateStatus.ISSUED,
        )
        self.assertEqual(cert.certificate_number, "CERT-1")
        self.assertIsNotNone(cert.issued_at)

    def test_notification_list(self):
        Notification.objects.create(
            user=self.student_user,
            title="Bem-vindo",
            message="Portal ativo",
        )
        self.client.login(username="aluno1", password="complex-pass-123")
        response = self.client.get(reverse("academics:notifications"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bem-vindo")
        self.assertFalse(
            Notification.objects.filter(user=self.student_user, is_read=False).exists()
        )


class StaffAcademicWorkflowTests(AcademicsFixturesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser(
            username="admin1", password="complex-pass-123", email="admin@example.com"
        )
        from django.contrib.auth.models import Group

        from apps.accounts.roles import STUDENT

        group, _ = Group.objects.get_or_create(name=STUDENT)
        self.student_user.groups.add(group)

    def test_create_timetable_slot(self):
        self.client.login(username="admin1", password="complex-pass-123")
        response = self.client.post(
            reverse("academics:dashboard_timetable_create"),
            {
                "classroom": self.classroom.pk,
                "subject": self.subject.pk,
                "teacher": self.teacher.pk,
                "weekday": Weekday.MONDAY,
                "start_time": "08:00",
                "end_time": "09:30",
                "room": "A1",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            TimetableSlot.objects.filter(classroom=self.classroom, room="A1").exists()
        )

    def test_issue_certificate_and_student_print(self):
        self.client.login(username="admin1", password="complex-pass-123")
        response = self.client.post(
            reverse("academics:dashboard_certificate_create"),
            {
                "student": self.student.pk,
                "title": "Conclusão",
                "academic_year": self.year.pk,
                "status": CertificateStatus.ISSUED,
            },
        )
        self.assertEqual(response.status_code, 302)
        cert = Certificate.objects.get(student=self.student)
        self.assertTrue(cert.certificate_number.startswith("CERT-"))
        self.client.logout()
        self.client.login(username="aluno1", password="complex-pass-123")
        printed = self.client.get(reverse("academics:certificate_print", args=[cert.pk]))
        self.assertEqual(printed.status_code, 200)
        self.assertContains(printed, "Conclusão")
        self.assertContains(printed, "João")

    def test_student_cannot_print_other_certificate(self):
        other = Student.objects.create(
            student_number="S-902", first_name="Outra", last_name="Pessoa"
        )
        cert = Certificate.objects.create(
            student=other,
            title="Outro",
            certificate_number="CERT-OTHER",
            status=CertificateStatus.ISSUED,
        )
        self.client.login(username="aluno1", password="complex-pass-123")
        response = self.client.get(reverse("academics:certificate_print", args=[cert.pk]))
        self.assertEqual(response.status_code, 403)

    def test_send_notification_to_students(self):
        self.client.login(username="admin1", password="complex-pass-123")
        response = self.client.post(
            reverse("academics:dashboard_notifications"),
            {
                "title": "Aviso",
                "message": "Aula amanhã",
                "audience": "students",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Notification.objects.filter(
                user=self.student_user, title="Aviso"
            ).exists()
        )

    def test_advanced_csv_reports(self):
        AttendanceRecord.objects.create(
            student=self.student,
            classroom=self.classroom,
            subject=self.subject,
            date=timezone.localdate(),
            status=AttendanceStatus.PRESENT,
            recorded_by=self.teacher,
        )
        self.client.login(username="admin1", password="complex-pass-123")
        attendance = self.client.get(reverse("accounts:report_attendance_csv"))
        self.assertEqual(attendance.status_code, 200)
        self.assertIn("S-900", attendance.content.decode("utf-8"))
        grades = self.client.get(reverse("accounts:report_grades_csv"))
        self.assertEqual(grades.status_code, 200)
        apps = self.client.get(reverse("accounts:report_applications_csv"))
        self.assertEqual(apps.status_code, 200)
