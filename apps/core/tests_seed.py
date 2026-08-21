from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.models import School
from apps.courses.models import Course
from apps.students.models import Student
from apps.teachers.models import Teacher

User = get_user_model()


class SeedDemoTests(TestCase):
    def test_seed_demo_creates_portal_users(self):
        call_command("seed_demo")
        self.assertTrue(User.objects.filter(username="aluno1").exists())
        self.assertTrue(User.objects.filter(username="prof1").exists())
        self.assertTrue(Student.objects.filter(student_number="S-2026-001").exists())
        self.assertTrue(Teacher.objects.filter(employee_number="T-001").exists())
        self.assertTrue(Course.objects.filter(code="TVP").exists())
        school = School.get_solo()
        self.assertIn("Atauro", school.name)

        self.client.login(username="aluno1", password="DemoAluno2026!")
        student_home = self.client.get(reverse("academics:student_portal"))
        self.assertEqual(student_home.status_code, 200)
        self.assertContains(student_home, "João")

        self.client.logout()
        self.client.login(username="prof1", password="DemoProf2026!")
        teacher_home = self.client.get(reverse("academics:teacher_portal"))
        self.assertEqual(teacher_home.status_code, 200)
        self.assertContains(teacher_home, "Ana")
