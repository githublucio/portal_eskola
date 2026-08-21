from django.test import TestCase

from apps.courses.models import Department
from apps.teachers.models import Teacher, TeacherStatus


class TeacherModelTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(code="INF", name="Informática")

    def test_create_teacher(self):
        teacher = Teacher.objects.create(
            employee_number="t-001",
            first_name="Maria",
            last_name="Santos",
            department=self.dept,
            specialization="Redes",
            qualification="Licenciatura",
            status=TeacherStatus.ACTIVE,
        )
        self.assertEqual(teacher.employee_number, "T-001")
        self.assertEqual(teacher.full_name, "Maria Santos")
        self.assertEqual(str(teacher), "Santos, Maria")
