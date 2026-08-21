from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.db.models import Count, Q
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, TemplateView, UpdateView

from apps.academics.models import (
    AttendanceRecord,
    AttendanceStatus,
    GradeEntry,
    OnlineApplication,
    ApplicationSettings,
)
from apps.core.models import School
from apps.courses.models import Course
from apps.documents.models import Document
from apps.events.models import Event
from apps.gallery.models import GalleryAlbum
from apps.news.models import News
from apps.students.models import Enrollment, Student
from apps.teachers.models import Teacher

from .audit import log_action
from .crud import user_has_perm
from .forms import LoginForm, ProfileForm, StyledPasswordChangeForm
from .mixins import DashboardBaseMixin, PermissionOrSuperuserMixin
from .models import AuditLog, User
# Re-export report views for urls
from .reports import (  # noqa: F401
    ApplicationsCsvReportView,
    AttendanceCsvReportView,
    CoursesCsvReportView,
    EnrollmentsCsvReportView,
    GradesCsvReportView,
    StudentsCsvReportView,
    TeachersCsvReportView,
)


class PortalLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class PortalLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")


class ProfileView(DashboardBaseMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Perfil rai ona.")
        return super().form_valid(form)


class PortalPasswordChangeView(DashboardBaseMixin, PasswordChangeView):
    form_class = StyledPasswordChangeForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, "Liafuan-sekrétu troka ona.")
        return response


class DashboardHomeView(DashboardBaseMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cards = []

        def add_card(key, label, value, perm, url_name):
            if user.is_superuser or user.has_perm(perm):
                cards.append(
                    {
                        "key": key,
                        "label": label,
                        "value": value,
                        "url_name": url_name,
                    }
                )

        add_card(
            "students",
            "Estudante sira",
            Student.objects.count(),
            "students.view_student",
            "accounts:dashboard_students",
        )
        add_card(
            "teachers",
            "Profesór sira",
            Teacher.objects.count(),
            "teachers.view_teacher",
            "accounts:dashboard_teachers",
        )
        add_card(
            "courses",
            "Kursu sira",
            Course.objects.count(),
            "courses.view_course",
            "accounts:dashboard_courses",
        )
        add_card(
            "news",
            "Notísia sira",
            News.objects.count(),
            "news.view_news",
            "accounts:dashboard_news",
        )
        add_card(
            "enrollments",
            "Matríkula sira",
            Enrollment.objects.count(),
            "students.view_enrollment",
            "accounts:dashboard_students",
        )

        context["stat_cards"] = cards
        if user.is_superuser or user.has_perm("events.view_event"):
            context["upcoming_events"] = Event.objects.filter(
                start_at__gte=timezone.now()
            ).order_by("start_at")[:5]
        else:
            context["upcoming_events"] = []

        if user.is_superuser or user.has_perm("accounts.view_auditlog"):
            context["recent_activity"] = AuditLog.objects.select_related("user")[:8]
        else:
            context["recent_activity"] = []
        return context


class DashboardSectionListView(DashboardBaseMixin, PermissionOrSuperuserMixin, ListView):
    template_name = "dashboard/section_list.html"
    paginate_by = 20
    context_object_name = "rows"
    section_title = ""
    admin_url = ""
    columns = ()
    search_fields = ()
    create_url_name = ""
    edit_url_name = ""
    delete_url_name = ""
    add_permission = ""
    change_permission = ""
    delete_permission = ""
    edit_label = "Hadia"
    row_extra_url_name = ""
    row_extra_label = ""
    header_action_specs = ()
    back_url_name = ""
    back_label = "Fila"

    def get_create_url(self):
        if self.create_url_name and user_has_perm(self.request.user, self.add_permission):
            return reverse(self.create_url_name)
        return ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["section_title"] = self.section_title
        context["admin_url"] = self.admin_url
        context["show_admin_link"] = bool(self.admin_url) and user.is_superuser
        context["columns"] = self.columns
        context["q"] = self.request.GET.get("q", "").strip()
        context["can_add"] = user_has_perm(user, self.add_permission)
        context["can_change"] = user_has_perm(user, self.change_permission)
        context["can_delete"] = user_has_perm(user, self.delete_permission)
        context["can_remove"] = context["can_change"] or context["can_delete"]
        context["create_url"] = self.get_create_url()
        context["edit_url_name"] = self.edit_url_name
        context["delete_url_name"] = self.delete_url_name
        context["edit_label"] = self.edit_label
        context["row_extra_url_name"] = self.row_extra_url_name
        context["row_extra_label"] = self.row_extra_label
        context["header_actions"] = [
            {"label": label, "url": reverse(url_name)}
            for label, url_name, perm in self.header_action_specs
            if user_has_perm(user, perm)
        ]
        context["back_url"] = reverse(self.back_url_name) if self.back_url_name else ""
        context["back_label"] = self.back_label
        context["has_row_actions"] = bool(
            (self.edit_url_name and context["can_change"])
            or (self.delete_url_name and context["can_remove"])
            or self.row_extra_url_name
        )
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q and self.search_fields:
            query = Q()
            for field in self.search_fields:
                query |= Q(**{f"{field}__icontains": q})
            qs = qs.filter(query)
        return qs


class DashboardNewsView(DashboardSectionListView):
    model = News
    required_permissions = ("news.view_news",)
    section_title = "Notísia sira"
    admin_url = "/admin/news/news/"
    columns = ("title", "status", "published_at")
    search_fields = ("title", "slug", "summary")
    ordering = ("-published_at", "-created_at")
    create_url_name = "accounts:dashboard_news_create"
    edit_url_name = "accounts:dashboard_news_update"
    delete_url_name = "accounts:dashboard_news_delete"
    add_permission = "news.add_news"
    change_permission = "news.change_news"
    delete_permission = "news.delete_news"
    header_action_specs = (
        ("Kategoria", "accounts:dashboard_news_categories", "news.view_newscategory"),
    )

    def get_queryset(self):
        return super().get_queryset().select_related("category")


class DashboardEventsView(DashboardSectionListView):
    model = Event
    required_permissions = ("events.view_event",)
    section_title = "Eventu sira"
    admin_url = "/admin/events/event/"
    columns = ("title", "start_at", "status")
    search_fields = ("title", "location", "organizer")
    ordering = ("start_at",)
    create_url_name = "accounts:dashboard_events_create"
    edit_url_name = "accounts:dashboard_events_update"
    delete_url_name = "accounts:dashboard_events_delete"
    add_permission = "events.add_event"
    change_permission = "events.change_event"
    delete_permission = "events.delete_event"


class DashboardCoursesView(DashboardSectionListView):
    model = Course
    required_permissions = ("courses.view_course",)
    section_title = "Kursu sira"
    admin_url = "/admin/courses/course/"
    columns = ("code", "name", "department", "status")
    search_fields = ("code", "name", "qualification")
    ordering = ("name",)
    create_url_name = "accounts:dashboard_courses_create"
    edit_url_name = "accounts:dashboard_courses_update"
    delete_url_name = "accounts:dashboard_courses_delete"
    add_permission = "courses.add_course"
    change_permission = "courses.change_course"
    row_extra_url_name = "accounts:dashboard_course_subjects"
    row_extra_label = "Disiplina"

    def get_queryset(self):
        return super().get_queryset().select_related("department")


class DashboardStudentsView(DashboardSectionListView):
    model = Student
    required_permissions = ("students.view_student",)
    section_title = "Estudante sira"
    admin_url = "/admin/students/student/"
    columns = ("student_number", "full_name", "status")
    search_fields = ("student_number", "first_name", "last_name", "email")
    ordering = ("last_name", "first_name")
    create_url_name = "accounts:dashboard_students_create"
    edit_url_name = "accounts:dashboard_students_update"
    add_permission = "students.add_student"
    change_permission = "students.change_student"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Students see only their own record when linked.
        if user.has_role("STUDENT") and not user.is_superuser:
            if hasattr(user, "student_profile"):
                return qs.filter(pk=user.student_profile.pk)
            return qs.none()
        return qs


class DashboardTeachersView(DashboardSectionListView):
    model = Teacher
    required_permissions = ("teachers.view_teacher",)
    section_title = "Profesór sira"
    admin_url = "/admin/teachers/teacher/"
    columns = ("employee_number", "full_name", "department", "status")
    search_fields = ("employee_number", "first_name", "last_name", "email")
    ordering = ("last_name", "first_name")
    create_url_name = "accounts:dashboard_teachers_create"
    edit_url_name = "accounts:dashboard_teachers_update"
    add_permission = "teachers.add_teacher"
    change_permission = "teachers.change_teacher"

    def get_queryset(self):
        qs = super().get_queryset().select_related("department")
        user = self.request.user
        if user.has_role("TEACHER") and not (
            user.is_superuser
            or user.has_role("SCHOOL_ADMIN")
            or user.has_role("ACADEMIC_STAFF")
        ):
            if hasattr(user, "teacher_profile"):
                return qs.filter(pk=user.teacher_profile.pk)
        return qs


class DashboardDocumentsView(DashboardSectionListView):
    model = Document
    required_permissions = ("documents.view_document",)
    section_title = "Dokumentu sira"
    admin_url = "/admin/documents/document/"
    columns = ("title", "category", "is_public", "published_at")
    search_fields = ("title", "description")
    ordering = ("-published_at", "-created_at")
    create_url_name = "accounts:dashboard_documents_create"
    edit_url_name = "accounts:dashboard_documents_update"
    delete_url_name = "accounts:dashboard_documents_delete"
    add_permission = "documents.add_document"
    change_permission = "documents.change_document"
    delete_permission = "documents.delete_document"
    header_action_specs = (
        (
            "Kategoria",
            "accounts:dashboard_document_categories",
            "documents.view_documentcategory",
        ),
    )

    def get_queryset(self):
        return super().get_queryset().select_related("category")


class DashboardGalleryView(DashboardSectionListView):
    model = GalleryAlbum
    required_permissions = ("gallery.view_galleryalbum",)
    section_title = "Imajen sira"
    admin_url = "/admin/gallery/galleryalbum/"
    columns = ("title", "status", "published_at")
    search_fields = ("title", "description")
    ordering = ("-published_at", "-created_at")
    create_url_name = "accounts:dashboard_gallery_create"
    edit_url_name = "accounts:dashboard_gallery_update"
    delete_url_name = "accounts:dashboard_gallery_delete"
    add_permission = "gallery.add_galleryalbum"
    change_permission = "gallery.change_galleryalbum"
    delete_permission = "gallery.delete_galleryalbum"
    row_extra_url_name = "accounts:dashboard_gallery_photos"
    row_extra_label = "Foto"


class DashboardUsersView(DashboardSectionListView):
    model = User
    required_permissions = ("accounts.view_user",)
    section_title = "Uza-na'in sira"
    admin_url = "/admin/accounts/user/"
    columns = ("username", "email", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name", "display_name")
    ordering = ("username",)
    create_url_name = "accounts:dashboard_users_create"
    edit_url_name = "accounts:dashboard_users_update"
    add_permission = "accounts.add_user"
    change_permission = "accounts.change_user"

    def get_queryset(self):
        qs = super().get_queryset()
        # School admins: limited — no other superusers.
        user = self.request.user
        if not user.is_superuser:
            qs = qs.filter(is_superuser=False)
        return qs


class DashboardAuditView(DashboardSectionListView):
    model = AuditLog
    required_permissions = ("accounts.view_auditlog",)
    section_title = "Rejistu audit"
    admin_url = "/admin/accounts/auditlog/"
    columns = ("created_at", "user", "action", "object_type", "message")
    search_fields = ("message", "object_repr", "object_type", "user__username")
    ordering = ("-created_at",)
    template_name = "dashboard/audit_list.html"

    def get_queryset(self):
        qs = super().get_queryset().select_related("user")
        action = self.request.GET.get("action", "").strip()
        if action:
            qs = qs.filter(action=action)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_choices"] = AuditLog.Action.choices
        context["selected_action"] = self.request.GET.get("action", "").strip()
        context["action_counts"] = (
            AuditLog.objects.values("action")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        return context


class DashboardApplicationsView(DashboardSectionListView):
    model = OnlineApplication
    required_permissions = ("academics.view_onlineapplication",)
    section_title = "Kandidatura sira"
    admin_url = "/admin/academics/onlineapplication/"
    columns = ("full_name", "email", "desired_course", "status", "created_at")
    search_fields = ("full_name", "email", "phone", "desired_course_text")
    ordering = ("-created_at",)
    edit_url_name = "accounts:dashboard_application_status"
    edit_label = "Estadu"
    change_permission = "academics.change_onlineapplication"
    header_action_specs = (
        (
            "Kritériu",
            "accounts:dashboard_application_criteria",
            "academics.view_applicationcriterion",
        ),
        (
            "Form aktivu/taka",
            "accounts:dashboard_application_settings",
            "academics.change_applicationsettings",
        ),
    )

    def get_queryset(self):
        return super().get_queryset().select_related("desired_course")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = ApplicationSettings.get_solo()
        context["section_title"] = (
            f"Kandidatura sira — "
            f"{'ATIVU' if settings.is_accepting else 'TAKA'}"
        )
        return context


class DashboardReportsView(DashboardBaseMixin, TemplateView):
    template_name = "dashboard/reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        exports = []

        def add(label, url_name, perm, count):
            if user.is_superuser or user.has_perm(perm):
                exports.append(
                    {"label": label, "url_name": url_name, "count": count}
                )

        add(
            "Estudante sira (CSV)",
            "accounts:report_students_csv",
            "students.view_student",
            Student.objects.count(),
        )
        add(
            "Profesór sira (CSV)",
            "accounts:report_teachers_csv",
            "teachers.view_teacher",
            Teacher.objects.count(),
        )
        add(
            "Matríkula sira (CSV)",
            "accounts:report_enrollments_csv",
            "students.view_enrollment",
            Enrollment.objects.count(),
        )
        add(
            "Kursu sira (CSV)",
            "accounts:report_courses_csv",
            "courses.view_course",
            Course.objects.count(),
        )
        add(
            "Asisténsia (CSV)",
            "accounts:report_attendance_csv",
            "academics.view_attendancerecord",
            AttendanceRecord.objects.count(),
        )
        add(
            "Nota sira (CSV)",
            "accounts:report_grades_csv",
            "academics.view_gradeentry",
            GradeEntry.objects.count(),
        )
        add(
            "Kandidatura sira (CSV)",
            "accounts:report_applications_csv",
            "academics.view_onlineapplication",
            OnlineApplication.objects.count(),
        )
        context["exports"] = exports
        attendance_total = AttendanceRecord.objects.count()
        attendance_present = AttendanceRecord.objects.filter(
            status=AttendanceStatus.PRESENT
        ).count()
        context["summary"] = {
            "students_active": Student.objects.filter(status="active").count(),
            "teachers_active": Teacher.objects.filter(status="active").count(),
            "courses_published": Course.objects.filter(status="published").count(),
            "enrollments_active": Enrollment.objects.filter(status="active").count(),
            "applications_new": OnlineApplication.objects.filter(status="new").count(),
            "attendance_present_pct": (
                round(attendance_present * 100 / attendance_total, 1)
                if attendance_total
                else 0
            ),
            "audit_last_7_days": AuditLog.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
        }
        return context


class DashboardSettingsView(DashboardBaseMixin, PermissionOrSuperuserMixin, UpdateView):
    model = School
    template_name = "dashboard/settings.html"
    success_url = reverse_lazy("accounts:dashboard_settings")
    required_permissions = ("core.change_school",)
    fields = (
        "name",
        "short_name",
        "logo",
        "description",
        "history",
        "vision",
        "mission",
        "address",
        "phone",
        "email",
        "facebook_url",
        "instagram_url",
        "youtube_url",
        "map_latitude",
        "map_longitude",
    )

    def get_object(self, queryset=None):
        return School.get_solo()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            css = "form-control"
            if field.widget.__class__.__name__ == "CheckboxInput":
                css = "form-check-input"
            field.widget.attrs.setdefault("class", css)
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            user=self.request.user,
            action=AuditLog.Action.UPDATE,
            obj=self.object,
            message="Konfigurasaun eskola hadia",
            request=self.request,
        )
        messages.success(self.request, "Konfigurasaun eskola rai ona.")
        return response
