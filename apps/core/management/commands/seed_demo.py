from datetime import date, time, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.academics.models import (
    AttendanceRecord,
    AttendanceStatus,
    Certificate,
    CertificateStatus,
    GradeEntry,
    Notification,
    TimetableSlot,
    Weekday,
)
from apps.core.models import School
from apps.courses.models import AcademicYear, Course, Department, PublishStatus, Subject
from apps.events.models import Event
from apps.events.models import PublishStatus as EventStatus
from apps.news.models import News, NewsCategory
from apps.news.models import PublishStatus as NewsStatus
from apps.students.models import (
    ClassRoom,
    Enrollment,
    EnrollmentStatus,
    Student,
    StudentClass,
    StudentClassStatus,
)
from apps.teachers.models import Teacher

User = get_user_model()

DEMO_PASSWORD_STUDENT = "DemoAluno2026!"
DEMO_PASSWORD_TEACHER = "DemoProf2026!"


class Command(BaseCommand):
    help = "Load demo school data for local testing (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-demo-users",
            action="store_true",
            help="Reset passwords for demo aluno/prof users.",
        )

    def handle(self, *args, **options):
        call_command("setup_roles")
        school = self._seed_school()
        dept = self._seed_department()
        year = self._seed_year()
        course, subjects = self._seed_course(dept)
        teacher, teacher_user = self._seed_teacher(dept, options["reset_demo_users"])
        student, student_user = self._seed_student(options["reset_demo_users"])
        classroom = self._seed_classroom(course, year, teacher)
        self._seed_enrollment(student, course, year)
        self._seed_student_class(student, classroom, year)
        self._seed_timetable(classroom, subjects, teacher)
        self._seed_attendance_grades(student, classroom, subjects, year, teacher)
        self._seed_certificate(student, year)
        self._seed_notifications(student_user, teacher_user)
        self._seed_cms(teacher_user)
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("")
        self.stdout.write(f"School: {school.short_name}")
        self.stdout.write(f"Student login: aluno1 / {DEMO_PASSWORD_STUDENT}")
        self.stdout.write(f"Teacher login: prof1 / {DEMO_PASSWORD_TEACHER}")
        self.stdout.write("Portals:")
        self.stdout.write("  http://127.0.0.1:8001/portal/student/")
        self.stdout.write("  http://127.0.0.1:8001/portal/teacher/")

    def _seed_school(self):
        school = School.get_solo()
        school.name = "Eskola Sekundária Téknika Vokasionál Públika Atauro"
        school.short_name = "ESTVP Atauro"
        school.description = (
            "Eskola sekundária téknika vokasionál públika iha Atauro, "
            "ho formasaun prátika no kompeténsia ba joven sira iha komunidade."
        )
        school.history = (
            "Eskola ne'e servisu ba komunidade Atauro ho formasaun téknika "
            "vokasionál públika, sustentabilidade no empregu lokál."
        )
        school.vision = (
            "Sai referénsia iha edukasaun téknika vokasionál públika iha Atauro."
        )
        school.mission = (
            "Forma joven sira ho kompeténsia téknika, disiplina no servisu "
            "ba komunidade."
        )
        school.address = "Vila, Atauro, Timor-Leste"
        school.phone = "+670 0000 0000"
        school.email = "info@estvp-atauro.local"
        if school.map_latitude is None or school.map_longitude is None:
            school.map_latitude = "-8.266700"
            school.map_longitude = "125.608300"
        logo_src = Path(settings.BASE_DIR) / "static" / "img" / "logo-eskola.png"
        if logo_src.exists() and not school.logo:
            from django.core.files import File

            with logo_src.open("rb") as fh:
                school.logo.save("logo-eskola.png", File(fh), save=False)
        school.save()
        return school

    def _seed_department(self):
        dept = Department.objects.filter(code__in=["PES", "FORM"]).first()
        if dept is None:
            dept = Department(code="FORM")
        dept.code = "FORM"
        dept.name = "Formasaun Téknika"
        dept.description = (
            "Departamentu formasaun téknika no vokasionál ESTVP Atauro."
        )
        dept.is_active = True
        dept.save()
        return dept

    def _seed_year(self):
        year, _ = AcademicYear.objects.get_or_create(
            name="2025/2026",
            defaults={
                "start_date": date(2025, 9, 1),
                "end_date": date(2026, 7, 31),
                "is_active": True,
            },
        )
        if not year.is_active:
            year.is_active = True
            year.save()
        return year

    def _seed_course(self, dept):
        course = Course.objects.filter(code__in=["PESKA", "TVP"]).first()
        if course is None:
            course = Course(code="TVP", department=dept)
        course.department = dept
        course.code = "TVP"
        course.name = "Tékniku Vokasionál"
        course.slug = "tecnico-vocacional"
        course.description = (
            "Kursu tékniku vokasionál Eskola Sekundária Téknika "
            "Vokasionál Públika Atauro, ho formasaun prátika no "
            "kompeténsia ba merkadu servisu."
        )
        course.duration = "tinan 3"
        course.qualification = "Sertifikadu Tékniku Vokasionál"
        course.requirements = "Remata ona ensinamentu báziku."
        course.status = PublishStatus.PUBLISHED
        course.save()
        subjects = []
        for code, name, semester in [
            ("MAT1", "Matemátika Aplikada", 1),
            ("POR1", "Lian Portugés", 1),
            ("PRA1", "Prátika Téknika I", 2),
        ]:
            subject = Subject.objects.filter(course=course, code=code).first()
            if subject is None and code == "MAT1":
                subject = Subject.objects.filter(course=course, code="BIO1").first()
            if subject is None and code == "POR1":
                subject = Subject.objects.filter(course=course, code="SEG1").first()
            if subject is None:
                subject = Subject(course=course, code=code)
            subject.course = course
            subject.code = code
            subject.name = name
            subject.semester = semester
            subject.credits = 4
            subject.is_active = True
            subject.save()
            subjects.append(subject)
        return course, subjects

    def _seed_teacher(self, dept, reset_password):
        user, created = User.objects.get_or_create(
            username="prof1",
            defaults={
                "email": "prof1@estvp-atauro.local",
                "first_name": "Ana",
                "last_name": "Costa",
                "display_name": "Ana Costa",
                "is_staff": True,
            },
        )
        if created or reset_password:
            user.set_password(DEMO_PASSWORD_TEACHER)
            user.is_staff = True
        user.email = "prof1@estvp-atauro.local"
        user.save()
        group = Group.objects.filter(name="TEACHER").first()
        if group:
            user.groups.add(group)
        teacher, _ = Teacher.objects.get_or_create(
            employee_number="T-001",
            defaults={
                "user": user,
                "first_name": "Ana",
                "last_name": "Costa",
                "email": user.email,
                "department": dept,
                "specialization": "Formasaun téknika vokasionál",
                "qualification": "Lisensiatura",
            },
        )
        teacher.user = user
        teacher.email = user.email
        teacher.department = dept
        teacher.specialization = "Formasaun téknika vokasionál"
        teacher.save()
        return teacher, user

    def _seed_student(self, reset_password):
        user, created = User.objects.get_or_create(
            username="aluno1",
            defaults={
                "email": "aluno1@estvp-atauro.local",
                "first_name": "João",
                "last_name": "Pereira",
                "display_name": "João Pereira",
            },
        )
        if created or reset_password:
            user.set_password(DEMO_PASSWORD_STUDENT)
        user.email = "aluno1@estvp-atauro.local"
        user.save()
        group = Group.objects.filter(name="STUDENT").first()
        if group:
            user.groups.add(group)
        student, _ = Student.objects.get_or_create(
            student_number="S-2026-001",
            defaults={
                "user": user,
                "first_name": "João",
                "last_name": "Pereira",
                "email": user.email,
                "phone": "+670 7711 0001",
            },
        )
        student.user = user
        student.email = user.email
        student.save()
        return student, user

    def _seed_classroom(self, course, year, teacher):
        classroom = ClassRoom.objects.filter(
            course=course,
            academic_year=year,
            name__in=["PESKA-A", "TVP-A"],
        ).first()
        if classroom is None:
            classroom = ClassRoom(course=course, academic_year=year, name="TVP-A")
        classroom.name = "TVP-A"
        classroom.level = classroom.level or 1
        classroom.capacity = classroom.capacity or 30
        classroom.adviser = teacher
        classroom.is_active = True
        classroom.save()
        return classroom

    def _seed_enrollment(self, student, course, year):
        Enrollment.objects.get_or_create(
            student=student,
            course=course,
            academic_year=year,
            defaults={
                "enrollment_number": "ENR-20252026-S2026001",
                "enrollment_date": date(2025, 9, 5),
                "status": EnrollmentStatus.ACTIVE,
            },
        )

    def _seed_student_class(self, student, classroom, year):
        StudentClass.objects.get_or_create(
            student=student,
            classroom=classroom,
            academic_year=year,
            defaults={
                "status": StudentClassStatus.ACTIVE,
                "assigned_at": date(2025, 9, 8),
            },
        )

    def _seed_timetable(self, classroom, subjects, teacher):
        slots = [
            (Weekday.MONDAY, time(8, 0), time(9, 30), subjects[0], "Sala 1"),
            (Weekday.WEDNESDAY, time(10, 0), time(11, 30), subjects[1], "Sala 2"),
            (Weekday.FRIDAY, time(8, 0), time(10, 0), subjects[2], "Sala prátika"),
        ]
        for weekday, start, end, subject, room in slots:
            slot, _ = TimetableSlot.objects.get_or_create(
                classroom=classroom,
                subject=subject,
                weekday=weekday,
                start_time=start,
                defaults={
                    "end_time": end,
                    "teacher": teacher,
                    "room": room,
                    "is_active": True,
                },
            )
            if slot.room != room or slot.teacher_id != teacher.pk:
                slot.room = room
                slot.teacher = teacher
                slot.end_time = end
                slot.is_active = True
                slot.save()

    def _seed_attendance_grades(self, student, classroom, subjects, year, teacher):
        today = timezone.localdate()
        for offset, subject, status in [
            (1, subjects[0], AttendanceStatus.PRESENT),
            (2, subjects[1], AttendanceStatus.LATE),
            (3, subjects[0], AttendanceStatus.PRESENT),
            (4, subjects[2], AttendanceStatus.ABSENT),
        ]:
            AttendanceRecord.objects.get_or_create(
                student=student,
                classroom=classroom,
                subject=subject,
                date=today - timedelta(days=offset),
                defaults={
                    "status": status,
                    "recorded_by": teacher,
                },
            )
        GradeEntry.objects.filter(
            student=student,
            subject=subjects[0],
            classroom=classroom,
            academic_year=year,
            term=1,
            assessment_name="Teste 1",
        ).update(assessment_name="Avaliasaun 1")
        GradeEntry.objects.filter(
            student=student,
            subject=subjects[1],
            classroom=classroom,
            academic_year=year,
            term=1,
            assessment_name__in=["Prática", "Prátika"],
        ).update(assessment_name="Prátika")
        GradeEntry.objects.get_or_create(
            student=student,
            subject=subjects[0],
            classroom=classroom,
            academic_year=year,
            term=1,
            assessment_name="Avaliasaun 1",
            defaults={
                "score": 86,
                "max_score": 100,
                "recorded_by": teacher,
            },
        )
        GradeEntry.objects.get_or_create(
            student=student,
            subject=subjects[1],
            classroom=classroom,
            academic_year=year,
            term=1,
            assessment_name="Prátika",
            defaults={
                "score": 78,
                "max_score": 100,
                "recorded_by": teacher,
            },
        )

    def _seed_certificate(self, student, year):
        cert, _ = Certificate.objects.get_or_create(
            certificate_number="CERT-DEMO-001",
            defaults={
                "student": student,
                "title": "Sertifikadu Asisténsia — Períodu 1",
                "academic_year": year,
                "status": CertificateStatus.ISSUED,
                "issued_at": timezone.localdate(),
            },
        )
        cert.title = "Sertifikadu Asisténsia — Períodu 1"
        cert.student = student
        cert.academic_year = year
        cert.status = CertificateStatus.ISSUED
        cert.save()

    def _seed_notifications(self, student_user, teacher_user):
        student_note, _ = Notification.objects.get_or_create(
            user=student_user,
            link="/portal/student/",
            defaults={
                "title": "Bemvindu ba portal estudante",
                "message": "Ita bele haree nota, asisténsia, oráriu no sertifikadu.",
            },
        )
        student_note.title = "Bemvindu ba portal estudante"
        student_note.message = (
            "Ita bele haree nota, asisténsia, oráriu no sertifikadu."
        )
        student_note.save()
        teacher_note, _ = Notification.objects.get_or_create(
            user=teacher_user,
            link="/portal/teacher/",
            defaults={
                "title": "Bemvindu ba portal profesór",
                "message": "Haree turma, oráriu no rezumu asisténsia.",
            },
        )
        teacher_note.title = "Bemvindu ba portal profesór"
        teacher_note.message = "Haree turma, oráriu no rezumu asisténsia."
        teacher_note.save()

    def _seed_cms(self, author):
        category, _ = NewsCategory.objects.get_or_create(
            slug="avisos",
            defaults={"name": "Avisu sira"},
        )
        category.name = "Avisu sira"
        category.save()
        news, _ = News.objects.get_or_create(
            slug="abertura-ano-letivo-2025-2026",
            defaults={
                "title": "Loke tinan eskola 2025/2026",
                "category": category,
                "summary": "Bemvindu estudante no família sira ba tinan eskola foun.",
                "content": "",
                "status": NewsStatus.PUBLISHED,
                "is_announcement": True,
                "author": author,
            },
        )
        news.title = "Loke tinan eskola 2025/2026"
        news.category = category
        news.summary = (
            "Bemvindu estudante no família sira ba Eskola Sekundária Téknika "
            "Vokasionál Públika Atauro."
        )
        news.content = (
            "Direksaun Eskola Sekundária Téknika Vokasionál Públika Atauro "
            "fó bemvindu ba komunidade eskola tomak. Aula hahú tuir oráriu "
            "ne'ebé publika iha portal."
        )
        news.status = NewsStatus.PUBLISHED
        news.is_announcement = True
        news.author = author
        news.save()
        event = Event.objects.filter(
            slug__in=["dia-aberto-peska", "dia-aberto-estvp"]
        ).first()
        if event is None:
            event = Event(slug="dia-aberto-estvp")
        event.slug = "dia-aberto-estvp"
        event.title = "Loron loke — ESTVP Atauro"
        event.description = (
            "Vizita ba instalasaun Eskola Sekundária Téknika Vokasionál "
            "Públika Atauro, demonstrasaun prátika no informasaun kona-ba "
            "kandidatura."
        )
        event.location = "Kampus ESTVP Atauro"
        event.organizer = "Direksaun eskola"
        if event.pk is None:
            event.start_at = timezone.now() + timedelta(days=14)
        event.status = EventStatus.PUBLISHED
        event.author = author
        event.save()
