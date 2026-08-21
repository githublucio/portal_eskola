from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from apps.core.models import School
from apps.news.models import News, NewsCategory
from apps.students.models import Student

from .models import AuditLog
from apps.accounts.rbac import (
    apply_default_role_permissions,
    apply_matrix_selection,
    get_role_group,
    matrix_rows,
)
from .roles import EDITOR, SCHOOL_ADMIN, STUDENT, TEACHER

User = get_user_model()


class CustomUserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="staffdemo",
            email="staff@example.com",
            password="complex-pass-123",
        )
        self.assertEqual(user.username, "staffdemo")
        self.assertTrue(user.check_password("complex-pass-123"))
        self.assertFalse(user.is_staff)
        self.assertEqual(user.public_name, "staffdemo")


class AuthAndDashboardTests(TestCase):
    def setUp(self):
        School.get_solo()
        self.password = "complex-pass-123"
        self.editor = User.objects.create_user(
            username="editor1",
            password=self.password,
            is_staff=True,
        )
        group, _ = Group.objects.get_or_create(name=EDITOR)
        perms = Permission.objects.filter(
            codename__in=["view_news", "add_news", "change_news"]
        )
        group.permissions.set(perms)
        self.editor.groups.add(group)

        self.student_user = User.objects.create_user(
            username="student1",
            password=self.password,
        )
        student_group, _ = Group.objects.get_or_create(name=STUDENT)
        self.student_user.groups.add(student_group)
        Student.objects.create(
            student_number="S-500",
            first_name="Lua",
            last_name="Costa",
            user=self.student_user,
        )

    def test_login_and_audit_log(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "editor1", "password": self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            AuditLog.objects.filter(
                user=self.editor, action=AuditLog.Action.LOGIN
            ).exists()
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_editor_sees_news_not_students(self):
        self.client.login(username="editor1", password=self.password)
        news = self.client.get(reverse("accounts:dashboard_news"))
        self.assertEqual(news.status_code, 200)
        students = self.client.get(reverse("accounts:dashboard_students"))
        self.assertEqual(students.status_code, 403)

    def test_student_only_own_record(self):
        other = Student.objects.create(
            student_number="S-501",
            first_name="Outro",
            last_name="Aluno",
        )
        # Give student view permission for the page itself
        perm = Permission.objects.get(codename="view_student")
        student_group = Group.objects.get(name=STUDENT)
        student_group.permissions.add(perm)

        self.client.login(username="student1", password=self.password)
        response = self.client.get(reverse("accounts:dashboard_students"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lua")
        self.assertNotContains(response, other.first_name)

    def test_nav_login_link_on_public_site(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, reverse("accounts:login"))

    def test_editor_can_create_news(self):
        category = NewsCategory.objects.create(name="Geral", slug="geral")
        self.client.login(username="editor1", password=self.password)
        url = reverse("accounts:dashboard_news_create")
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(
            url,
            {
                "title": "Notísia foun",
                "category": category.pk,
                "content": "Konteúdu notísia",
                "status": "draft",
                "summary": "Rezumu",
            },
        )
        self.assertEqual(response.status_code, 302)
        news = News.objects.get(title="Notísia foun")
        self.assertEqual(news.status, "draft")
        self.assertEqual(news.author, self.editor)
        self.assertTrue(
            AuditLog.objects.filter(
                user=self.editor,
                action=AuditLog.Action.CREATE,
                object_type="News",
            ).exists()
        )

    def test_editor_cannot_publish_without_permission(self):
        category = NewsCategory.objects.create(name="Geral", slug="geral")
        self.client.login(username="editor1", password=self.password)
        response = self.client.post(
            reverse("accounts:dashboard_news_create"),
            {
                "title": "Publika la bele",
                "category": category.pk,
                "content": "Konteúdu",
                "status": "published",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(News.objects.filter(title="Publika la bele").exists())

    def test_student_cannot_create_news(self):
        category = NewsCategory.objects.create(name="Geral", slug="geral")
        self.client.login(username="student1", password=self.password)
        url = reverse("accounts:dashboard_news_create")
        self.assertEqual(self.client.get(url).status_code, 403)
        response = self.client.post(
            url,
            {
                "title": "Hack",
                "category": category.pk,
                "content": "La bele",
                "status": "published",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(News.objects.filter(title="Hack").exists())

    def test_non_superuser_cannot_edit_superuser(self):
        admin_user = User.objects.create_user(
            username="schooladmin",
            password=self.password,
            is_staff=True,
        )
        group, _ = Group.objects.get_or_create(name=SCHOOL_ADMIN)
        perms = Permission.objects.filter(codename__in=["view_user", "change_user"])
        group.permissions.add(*perms)
        admin_user.groups.add(group)
        superuser = User.objects.create_superuser(
            username="rootadmin",
            email="root@example.com",
            password=self.password,
        )

        self.client.login(username="schooladmin", password=self.password)
        listing = self.client.get(reverse("accounts:dashboard_users"))
        self.assertEqual(listing.status_code, 200)
        self.assertNotContains(listing, "rootadmin")

        edit_url = reverse("accounts:dashboard_users_update", args=[superuser.pk])
        self.assertEqual(self.client.get(edit_url).status_code, 404)
        posted = self.client.post(
            edit_url,
            {
                "username": "hacked",
                "is_active": True,
            },
        )
        self.assertEqual(posted.status_code, 404)
        superuser.refresh_from_db()
        self.assertEqual(superuser.username, "rootadmin")


class RoleBasedAccessTests(TestCase):
    def setUp(self):
        School.get_solo()
        self.password = "complex-pass-123"
        self.admin = User.objects.create_superuser(
            username="rbacadmin",
            email="rbacadmin@example.com",
            password=self.password,
        )
        self.teacher = User.objects.create_user(
            username="rbacteacher",
            password=self.password,
        )
        teacher_group = get_role_group(TEACHER)
        apply_default_role_permissions(teacher_group)
        self.teacher.groups.add(teacher_group)

        self.school_admin = User.objects.create_user(
            username="rbacschool",
            password=self.password,
            is_staff=True,
        )
        school_group = get_role_group(SCHOOL_ADMIN)
        apply_default_role_permissions(school_group)
        self.school_admin.groups.add(school_group)

        self.editor = User.objects.create_user(
            username="rbaceditor",
            password=self.password,
            is_staff=True,
        )
        editor_group = get_role_group(EDITOR)
        apply_default_role_permissions(editor_group)
        self.editor.groups.add(editor_group)

    def test_matrix_keeps_unmanaged_permissions(self):
        group = get_role_group(TEACHER)
        extra = Permission.objects.get(codename="view_logentry")
        group.permissions.add(extra)
        apply_matrix_selection(group, {"news.view", "attendance.view"})
        keys = set(
            f"{perm.content_type.app_label}.{perm.codename}"
            for perm in group.permissions.all()
        )
        self.assertIn("news.view_news", keys)
        self.assertIn("admin.view_logentry", keys)
        self.assertNotIn("academics.add_attendancerecord", keys)

    def test_student_cannot_open_roles_page(self):
        student = User.objects.create_user(username="rbacstudent", password=self.password)
        student.groups.add(get_role_group(STUDENT))
        self.client.login(username="rbacstudent", password=self.password)
        response = self.client.get(reverse("accounts:dashboard_roles"))
        self.assertEqual(response.status_code, 403)

    def test_editor_cannot_open_roles_page(self):
        self.client.login(username="rbaceditor", password=self.password)
        response = self.client.get(reverse("accounts:dashboard_roles"))
        self.assertEqual(response.status_code, 403)

    def test_school_admin_can_view_but_not_edit_permissions(self):
        self.client.login(username="rbacschool", password=self.password)
        listing = self.client.get(reverse("accounts:dashboard_roles"))
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, "Teacher")
        self.assertNotContains(listing, "SUPER_ADMIN")

        url = reverse("accounts:dashboard_roles_update", args=[TEACHER])
        self.assertEqual(self.client.get(url).status_code, 200)
        posted = self.client.post(
            url,
            {"action": "save_permissions", "access": ["news.add"]},
        )
        self.assertEqual(posted.status_code, 403)
        self.assertFalse(
            get_role_group(TEACHER).permissions.filter(codename="add_news").exists()
        )

    def test_school_admin_can_assign_role_member(self):
        extra = User.objects.create_user(username="newstaff", password=self.password)
        self.client.login(username="rbacschool", password=self.password)
        url = reverse("accounts:dashboard_roles_update", args=[EDITOR])
        response = self.client.post(
            url,
            {"action": "add_member", "user_id": extra.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(extra.groups.filter(name=EDITOR).exists())

    def test_superuser_can_grant_teacher_news_create(self):
        group = get_role_group(TEACHER)
        selected = [
            cell["value"]
            for row in matrix_rows(group)
            for cell in row["cells"]
            if cell["checked"] and cell["value"]
        ]
        selected.append("news.add")
        self.client.login(username="rbacadmin", password=self.password)
        url = reverse("accounts:dashboard_roles_update", args=[TEACHER])
        response = self.client.post(
            url,
            {"action": "save_permissions", "access": selected},
        )
        self.assertEqual(response.status_code, 302)
        teacher = User.objects.get(pk=self.teacher.pk)
        self.assertTrue(teacher.has_perm("news.add_news"))

        self.client.logout()
        self.client.login(username="rbacteacher", password=self.password)
        create_url = reverse("accounts:dashboard_news_create")
        self.assertEqual(self.client.get(create_url).status_code, 200)

    def test_superuser_reset_defaults(self):
        group = get_role_group(TEACHER)
        apply_matrix_selection(group, {"news.add", "news.change"})
        self.assertTrue(group.permissions.filter(codename="add_news").exists())
        self.client.login(username="rbacadmin", password=self.password)
        response = self.client.post(
            reverse("accounts:dashboard_roles_update", args=[TEACHER]),
            {"action": "reset_defaults"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(get_role_group(TEACHER).permissions.filter(codename="add_news").exists())
        self.assertTrue(
            get_role_group(TEACHER).permissions.filter(codename="add_attendancerecord").exists()
        )

    def test_non_superuser_cannot_open_super_admin_role(self):
        self.client.login(username="rbacschool", password=self.password)
        url = reverse("accounts:dashboard_roles_update", args=["SUPER_ADMIN"])
        self.assertEqual(self.client.get(url).status_code, 404)
