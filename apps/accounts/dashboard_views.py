from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.views.generic import TemplateView

from apps.academics.models import (
    ApplicationCriterion,
    ApplicationSettings,
    OnlineApplication,
)
from apps.courses.models import Course, Subject
from apps.documents.models import Document, DocumentCategory
from apps.events.models import Event
from apps.gallery.models import GalleryAlbum, GalleryPhoto
from apps.news.models import News, NewsCategory
from apps.students.models import Student
from apps.teachers.models import Teacher

from .audit import log_action
from .crud import (
    DashboardCreateView,
    DashboardStatusDeleteView,
    DashboardUpdateView,
    StaffSectionMixin,
    user_has_perm,
)
from .dashboard_forms import (
    ApplicationCriterionForm,
    ApplicationSettingsForm,
    ApplicationStatusForm,
    CourseForm,
    DashboardUserCreateForm,
    DocumentCategoryForm,
    DocumentForm,
    EventForm,
    GalleryAlbumForm,
    GalleryPhotoForm,
    NewsCategoryForm,
    NewsForm,
    StudentForm,
    StyledDashboardUserChangeForm,
    SubjectForm,
    TeacherForm,
)
from .mixins import DashboardBaseMixin, PermissionOrSuperuserMixin
from .models import AuditLog, User
from .rbac import (
    apply_default_role_permissions,
    apply_matrix_selection,
    get_role_group,
    iter_role_summaries,
    matrix_rows,
    role_description,
    role_label,
)
from .roles import ALL_ROLES, SUPER_ADMIN
from .views import DashboardSectionListView


class DashboardNewsCreateView(DashboardCreateView):
    model = News
    form_class = NewsForm
    success_url = reverse_lazy("accounts:dashboard_news")
    required_permissions = ("news.add_news",)
    cancel_url_name = "accounts:dashboard_news"
    form_title = "Kria notísia"
    success_message = "Notísia kria ona."
    audit_message = "Notísia kria"
    author_field = "author"


class DashboardNewsUpdateView(DashboardUpdateView):
    model = News
    form_class = NewsForm
    success_url = reverse_lazy("accounts:dashboard_news")
    required_permissions = ("news.change_news",)
    cancel_url_name = "accounts:dashboard_news"
    form_title = "Hadia notísia"
    success_message = "Notísia hadia ona."
    audit_message = "Notísia hadia"


class DashboardNewsDeleteView(DashboardStatusDeleteView):
    model = News
    success_url = reverse_lazy("accounts:dashboard_news")
    cancel_url_name = "accounts:dashboard_news"
    required_permissions = ("news.change_news", "news.delete_news")
    change_permission = "news.change_news"
    delete_permission = "news.delete_news"
    archive_message = "Notísia arkivu ona."
    delete_message = "Notísia hamoos ona."


class DashboardNewsCategoryListView(DashboardSectionListView):
    model = NewsCategory
    required_permissions = ("news.view_newscategory",)
    section_title = "Kategoria notísia"
    columns = ("name", "slug")
    search_fields = ("name", "slug")
    ordering = ("name",)
    create_url_name = "accounts:dashboard_news_category_create"
    edit_url_name = "accounts:dashboard_news_category_update"
    delete_url_name = "accounts:dashboard_news_category_delete"
    add_permission = "news.add_newscategory"
    change_permission = "news.change_newscategory"
    delete_permission = "news.delete_newscategory"
    back_url_name = "accounts:dashboard_news"


class DashboardNewsCategoryCreateView(DashboardCreateView):
    model = NewsCategory
    form_class = NewsCategoryForm
    success_url = reverse_lazy("accounts:dashboard_news_categories")
    required_permissions = ("news.add_newscategory",)
    cancel_url_name = "accounts:dashboard_news_categories"
    form_title = "Kria kategoria notísia"
    success_message = "Kategoria kria ona."
    audit_message = "Kategoria notísia kria"


class DashboardNewsCategoryUpdateView(DashboardUpdateView):
    model = NewsCategory
    form_class = NewsCategoryForm
    success_url = reverse_lazy("accounts:dashboard_news_categories")
    required_permissions = ("news.change_newscategory",)
    cancel_url_name = "accounts:dashboard_news_categories"
    form_title = "Hadia kategoria notísia"
    success_message = "Kategoria hadia ona."
    audit_message = "Kategoria notísia hadia"


class DashboardNewsCategoryDeleteView(DashboardStatusDeleteView):
    model = NewsCategory
    success_url = reverse_lazy("accounts:dashboard_news_categories")
    cancel_url_name = "accounts:dashboard_news_categories"
    required_permissions = ("news.delete_newscategory",)
    prefer_archive = False
    allow_hard_delete = True
    delete_permission = "news.delete_newscategory"
    delete_message = "Kategoria hamoos ona."


class DashboardEventCreateView(DashboardCreateView):
    model = Event
    form_class = EventForm
    success_url = reverse_lazy("accounts:dashboard_events")
    required_permissions = ("events.add_event",)
    cancel_url_name = "accounts:dashboard_events"
    form_title = "Kria eventu"
    success_message = "Eventu kria ona."
    audit_message = "Eventu kria"
    author_field = "author"


class DashboardEventUpdateView(DashboardUpdateView):
    model = Event
    form_class = EventForm
    success_url = reverse_lazy("accounts:dashboard_events")
    required_permissions = ("events.change_event",)
    cancel_url_name = "accounts:dashboard_events"
    form_title = "Hadia eventu"
    success_message = "Eventu hadia ona."
    audit_message = "Eventu hadia"


class DashboardEventDeleteView(DashboardStatusDeleteView):
    model = Event
    success_url = reverse_lazy("accounts:dashboard_events")
    cancel_url_name = "accounts:dashboard_events"
    required_permissions = ("events.change_event", "events.delete_event")
    change_permission = "events.change_event"
    delete_permission = "events.delete_event"
    archive_message = "Eventu arkivu ona."
    delete_message = "Eventu hamoos ona."


class DashboardDocumentCreateView(DashboardCreateView):
    model = Document
    form_class = DocumentForm
    success_url = reverse_lazy("accounts:dashboard_documents")
    required_permissions = ("documents.add_document",)
    cancel_url_name = "accounts:dashboard_documents"
    form_title = "Kria dokumentu"
    success_message = "Dokumentu kria ona."
    audit_message = "Dokumentu kria"
    author_field = "uploaded_by"


class DashboardDocumentUpdateView(DashboardUpdateView):
    model = Document
    form_class = DocumentForm
    success_url = reverse_lazy("accounts:dashboard_documents")
    required_permissions = ("documents.change_document",)
    cancel_url_name = "accounts:dashboard_documents"
    form_title = "Hadia dokumentu"
    success_message = "Dokumentu hadia ona."
    audit_message = "Dokumentu hadia"


class DashboardDocumentDeleteView(DashboardStatusDeleteView):
    model = Document
    success_url = reverse_lazy("accounts:dashboard_documents")
    cancel_url_name = "accounts:dashboard_documents"
    required_permissions = ("documents.change_document", "documents.delete_document")
    change_permission = "documents.change_document"
    delete_permission = "documents.delete_document"
    archive_message = "Dokumentu arkivu ona."
    delete_message = "Dokumentu hamoos ona."


class DashboardDocumentCategoryListView(DashboardSectionListView):
    model = DocumentCategory
    required_permissions = ("documents.view_documentcategory",)
    section_title = "Kategoria dokumentu"
    columns = ("name", "slug")
    search_fields = ("name", "slug")
    ordering = ("name",)
    create_url_name = "accounts:dashboard_document_category_create"
    edit_url_name = "accounts:dashboard_document_category_update"
    delete_url_name = "accounts:dashboard_document_category_delete"
    add_permission = "documents.add_documentcategory"
    change_permission = "documents.change_documentcategory"
    delete_permission = "documents.delete_documentcategory"
    back_url_name = "accounts:dashboard_documents"


class DashboardDocumentCategoryCreateView(DashboardCreateView):
    model = DocumentCategory
    form_class = DocumentCategoryForm
    success_url = reverse_lazy("accounts:dashboard_document_categories")
    required_permissions = ("documents.add_documentcategory",)
    cancel_url_name = "accounts:dashboard_document_categories"
    form_title = "Kria kategoria dokumentu"
    success_message = "Kategoria kria ona."
    audit_message = "Kategoria dokumentu kria"


class DashboardDocumentCategoryUpdateView(DashboardUpdateView):
    model = DocumentCategory
    form_class = DocumentCategoryForm
    success_url = reverse_lazy("accounts:dashboard_document_categories")
    required_permissions = ("documents.change_documentcategory",)
    cancel_url_name = "accounts:dashboard_document_categories"
    form_title = "Hadia kategoria dokumentu"
    success_message = "Kategoria hadia ona."
    audit_message = "Kategoria dokumentu hadia"


class DashboardDocumentCategoryDeleteView(DashboardStatusDeleteView):
    model = DocumentCategory
    success_url = reverse_lazy("accounts:dashboard_document_categories")
    cancel_url_name = "accounts:dashboard_document_categories"
    required_permissions = ("documents.delete_documentcategory",)
    prefer_archive = False
    allow_hard_delete = True
    delete_permission = "documents.delete_documentcategory"
    delete_message = "Kategoria hamoos ona."


class DashboardGalleryCreateView(DashboardCreateView):
    model = GalleryAlbum
    form_class = GalleryAlbumForm
    success_url = reverse_lazy("accounts:dashboard_gallery")
    required_permissions = ("gallery.add_galleryalbum",)
    cancel_url_name = "accounts:dashboard_gallery"
    form_title = "Kria álbum"
    success_message = "Álbum kria ona."
    audit_message = "Álbum kria"


class DashboardGalleryUpdateView(DashboardUpdateView):
    model = GalleryAlbum
    form_class = GalleryAlbumForm
    success_url = reverse_lazy("accounts:dashboard_gallery")
    required_permissions = ("gallery.change_galleryalbum",)
    cancel_url_name = "accounts:dashboard_gallery"
    form_title = "Hadia álbum"
    success_message = "Álbum hadia ona."
    audit_message = "Álbum hadia"


class DashboardGalleryDeleteView(DashboardStatusDeleteView):
    model = GalleryAlbum
    success_url = reverse_lazy("accounts:dashboard_gallery")
    cancel_url_name = "accounts:dashboard_gallery"
    required_permissions = ("gallery.change_galleryalbum", "gallery.delete_galleryalbum")
    change_permission = "gallery.change_galleryalbum"
    delete_permission = "gallery.delete_galleryalbum"
    archive_message = "Álbum arkivu ona."
    delete_message = "Álbum hamoos ona."


class DashboardGalleryPhotoListView(DashboardSectionListView):
    model = GalleryPhoto
    required_permissions = ("gallery.view_galleryphoto", "gallery.view_galleryalbum")
    columns = ("caption", "sort_order")
    search_fields = ("caption",)
    ordering = ("sort_order", "id")
    edit_url_name = ""
    delete_url_name = "accounts:dashboard_gallery_photo_delete"
    add_permission = "gallery.add_galleryphoto"
    delete_permission = "gallery.delete_galleryphoto"
    back_url_name = "accounts:dashboard_gallery"

    def dispatch(self, request, *args, **kwargs):
        self.album = get_object_or_404(GalleryAlbum, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(album=self.album)

    def get_create_url(self):
        if user_has_perm(self.request.user, self.add_permission):
            return reverse("accounts:dashboard_gallery_photo_create", args=[self.album.pk])
        return ""

    def get_context_data(self, **kwargs):
        self.section_title = f"Foto — {self.album.title}"
        return super().get_context_data(**kwargs)


class DashboardGalleryPhotoCreateView(DashboardCreateView):
    model = GalleryPhoto
    form_class = GalleryPhotoForm
    required_permissions = ("gallery.add_galleryphoto",)
    form_title = "Kria foto"
    success_message = "Foto kria ona."
    audit_message = "Foto kria"

    def dispatch(self, request, *args, **kwargs):
        self.album = get_object_or_404(GalleryAlbum, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.album = self.album
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("accounts:dashboard_gallery_photos", args=[self.album.pk])

    def get_cancel_url(self):
        return reverse("accounts:dashboard_gallery_photos", args=[self.album.pk])


class DashboardGalleryPhotoDeleteView(DashboardStatusDeleteView):
    model = GalleryPhoto
    required_permissions = ("gallery.delete_galleryphoto",)
    prefer_archive = False
    allow_hard_delete = True
    delete_permission = "gallery.delete_galleryphoto"
    delete_message = "Foto hamoos ona."

    def get_success_url(self):
        return reverse("accounts:dashboard_gallery_photos", args=[self.object.album_id])

    def get_cancel_url(self):
        return reverse("accounts:dashboard_gallery_photos", args=[self.object.album_id])


class DashboardCourseCreateView(DashboardCreateView):
    model = Course
    form_class = CourseForm
    success_url = reverse_lazy("accounts:dashboard_courses")
    required_permissions = ("courses.add_course",)
    cancel_url_name = "accounts:dashboard_courses"
    form_title = "Kria kursu"
    success_message = "Kursu kria ona."
    audit_message = "Kursu kria"


class DashboardCourseUpdateView(DashboardUpdateView):
    model = Course
    form_class = CourseForm
    success_url = reverse_lazy("accounts:dashboard_courses")
    required_permissions = ("courses.change_course",)
    cancel_url_name = "accounts:dashboard_courses"
    form_title = "Hadia kursu"
    success_message = "Kursu hadia ona."
    audit_message = "Kursu hadia"


class DashboardCourseDeleteView(DashboardStatusDeleteView):
    model = Course
    success_url = reverse_lazy("accounts:dashboard_courses")
    cancel_url_name = "accounts:dashboard_courses"
    required_permissions = ("courses.change_course",)
    prefer_archive = True
    allow_hard_delete = False
    change_permission = "courses.change_course"
    archive_message = "Kursu arkivu ona."


class DashboardCourseSubjectListView(DashboardSectionListView):
    model = Subject
    required_permissions = ("courses.view_subject", "courses.view_course")
    columns = ("code", "name", "semester", "credits", "is_active")
    search_fields = ("code", "name")
    ordering = ("semester", "code")
    edit_url_name = "accounts:dashboard_subject_update"
    add_permission = "courses.add_subject"
    change_permission = "courses.change_subject"
    back_url_name = "accounts:dashboard_courses"

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(course=self.course)

    def get_create_url(self):
        if user_has_perm(self.request.user, self.add_permission):
            return reverse("accounts:dashboard_subject_create", args=[self.course.pk])
        return ""

    def get_context_data(self, **kwargs):
        self.section_title = f"Disiplina — {self.course.name}"
        return super().get_context_data(**kwargs)


class DashboardSubjectCreateView(DashboardCreateView):
    model = Subject
    form_class = SubjectForm
    required_permissions = ("courses.add_subject",)
    form_title = "Kria disiplina"
    success_message = "Disiplina kria ona."
    audit_message = "Disiplina kria"

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.course = self.course
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("accounts:dashboard_course_subjects", args=[self.course.pk])

    def get_cancel_url(self):
        return reverse("accounts:dashboard_course_subjects", args=[self.course.pk])


class DashboardSubjectUpdateView(DashboardUpdateView):
    model = Subject
    form_class = SubjectForm
    required_permissions = ("courses.change_subject",)
    form_title = "Hadia disiplina"
    success_message = "Disiplina hadia ona."
    audit_message = "Disiplina hadia"

    def get_success_url(self):
        return reverse("accounts:dashboard_course_subjects", args=[self.object.course_id])

    def get_cancel_url(self):
        return reverse("accounts:dashboard_course_subjects", args=[self.object.course_id])


class DashboardStudentCreateView(DashboardCreateView):
    model = Student
    form_class = StudentForm
    success_url = reverse_lazy("accounts:dashboard_students")
    required_permissions = ("students.add_student",)
    cancel_url_name = "accounts:dashboard_students"
    form_title = "Kria estudante"
    success_message = "Estudante kria ona."
    audit_message = "Estudante kria"


class DashboardStudentUpdateView(DashboardUpdateView):
    model = Student
    form_class = StudentForm
    success_url = reverse_lazy("accounts:dashboard_students")
    required_permissions = ("students.change_student",)
    cancel_url_name = "accounts:dashboard_students"
    form_title = "Hadia estudante"
    success_message = "Estudante hadia ona."
    audit_message = "Estudante hadia"

    def get_queryset(self):
        qs = Student.objects.all()
        user = self.request.user
        if user.has_role("STUDENT") and not user.is_superuser:
            if hasattr(user, "student_profile"):
                return qs.filter(pk=user.student_profile.pk)
            return qs.none()
        return qs


class DashboardTeacherCreateView(DashboardCreateView):
    model = Teacher
    form_class = TeacherForm
    success_url = reverse_lazy("accounts:dashboard_teachers")
    required_permissions = ("teachers.add_teacher",)
    cancel_url_name = "accounts:dashboard_teachers"
    form_title = "Kria profesór"
    success_message = "Profesór kria ona."
    audit_message = "Profesór kria"


class DashboardTeacherUpdateView(DashboardUpdateView):
    model = Teacher
    form_class = TeacherForm
    success_url = reverse_lazy("accounts:dashboard_teachers")
    required_permissions = ("teachers.change_teacher",)
    cancel_url_name = "accounts:dashboard_teachers"
    form_title = "Hadia profesór"
    success_message = "Profesór hadia ona."
    audit_message = "Profesór hadia"

    def get_queryset(self):
        qs = Teacher.objects.select_related("department")
        user = self.request.user
        if user.has_role("TEACHER") and not (
            user.is_superuser
            or user.has_role("SCHOOL_ADMIN")
            or user.has_role("ACADEMIC_STAFF")
        ):
            if hasattr(user, "teacher_profile"):
                return qs.filter(pk=user.teacher_profile.pk)
        return qs


class DashboardApplicationStatusView(DashboardUpdateView):
    model = OnlineApplication
    form_class = ApplicationStatusForm
    success_url = reverse_lazy("accounts:dashboard_applications")
    required_permissions = ("academics.change_onlineapplication",)
    cancel_url_name = "accounts:dashboard_applications"
    form_title = "Hadia estadu kandidatura"
    success_message = "Estadu kandidatura rai ona."
    audit_message = "Kandidatura estadu"

    def get_queryset(self):
        return OnlineApplication.objects.select_related("desired_course")

    def get_detail_rows(self):
        obj = self.object
        if obj.certificate_file:
            cert = format_html(
                '<a href="{}" target="_blank" rel="noopener">Haree arkivu</a>',
                obj.certificate_file.url,
            )
        else:
            cert = "—"
        return [
            ("Naran", obj.full_name),
            ("Korreiu", obj.email),
            ("Telefone", obj.phone),
            ("Data moris", obj.date_of_birth),
            ("Idade", obj.age),
            ("Eskola pre-sekundária", obj.previous_school),
            ("Kursu", obj.desired_course or obj.desired_course_text),
            ("Sertifikadu", cert),
            ("Estadu agora", obj.get_status_display()),
        ]


class DashboardApplicationSettingsView(DashboardUpdateView):
    model = ApplicationSettings
    form_class = ApplicationSettingsForm
    success_url = reverse_lazy("accounts:dashboard_applications")
    required_permissions = ("academics.change_applicationsettings",)
    cancel_url_name = "accounts:dashboard_applications"
    form_title = "Konfigurasaun formuláriu kandidatura"
    form_intro = (
        "Liga/desliga formuláriu publiku no define idade. "
        "Desliga bainhira pendaftaran remata ona."
    )
    success_message = "Konfigurasaun kandidatura rai ona."
    audit_message = "Konfigurasaun kandidatura"

    def get_object(self, queryset=None):
        return ApplicationSettings.get_solo()


class DashboardApplicationCriterionListView(DashboardSectionListView):
    model = ApplicationCriterion
    required_permissions = ("academics.view_applicationcriterion",)
    section_title = "Kritériu kandidatura"
    columns = ("text", "sort_order", "is_active")
    search_fields = ("text",)
    ordering = ("sort_order", "id")
    create_url_name = "accounts:dashboard_application_criterion_create"
    edit_url_name = "accounts:dashboard_application_criterion_update"
    delete_url_name = "accounts:dashboard_application_criterion_delete"
    add_permission = "academics.add_applicationcriterion"
    change_permission = "academics.change_applicationcriterion"
    delete_permission = "academics.delete_applicationcriterion"
    back_url_name = "accounts:dashboard_applications"
    header_action_specs = (
        (
            "Konfigurasaun form",
            "accounts:dashboard_application_settings",
            "academics.change_applicationsettings",
        ),
    )


class DashboardApplicationCriterionCreateView(DashboardCreateView):
    model = ApplicationCriterion
    form_class = ApplicationCriterionForm
    success_url = reverse_lazy("accounts:dashboard_application_criteria")
    required_permissions = ("academics.add_applicationcriterion",)
    cancel_url_name = "accounts:dashboard_application_criteria"
    form_title = "Kria kritériu"
    success_message = "Kritériu kria ona."
    audit_message = "Kritériu kandidatura kria"


class DashboardApplicationCriterionUpdateView(DashboardUpdateView):
    model = ApplicationCriterion
    form_class = ApplicationCriterionForm
    success_url = reverse_lazy("accounts:dashboard_application_criteria")
    required_permissions = ("academics.change_applicationcriterion",)
    cancel_url_name = "accounts:dashboard_application_criteria"
    form_title = "Hadia kritériu"
    success_message = "Kritériu rai ona."
    audit_message = "Kritériu kandidatura hadia"


class DashboardApplicationCriterionDeleteView(DashboardStatusDeleteView):
    model = ApplicationCriterion
    success_url = reverse_lazy("accounts:dashboard_application_criteria")
    cancel_url_name = "accounts:dashboard_application_criteria"
    required_permissions = (
        "academics.change_applicationcriterion",
        "academics.delete_applicationcriterion",
    )
    prefer_archive = False
    allow_hard_delete = True
    change_permission = "academics.change_applicationcriterion"
    delete_permission = "academics.delete_applicationcriterion"
    delete_message = "Kritériu hamoos ona."


class DashboardUserCreateView(DashboardCreateView):
    model = User
    form_class = DashboardUserCreateForm
    success_url = reverse_lazy("accounts:dashboard_users")
    required_permissions = ("accounts.add_user",)
    cancel_url_name = "accounts:dashboard_users"
    form_title = "Kria uza-na'in"
    success_message = "Uza-na'in kria ona."
    audit_message = "Uza-na'in kria"


class DashboardUserUpdateView(DashboardUpdateView):
    model = User
    form_class = StyledDashboardUserChangeForm
    success_url = reverse_lazy("accounts:dashboard_users")
    required_permissions = ("accounts.change_user",)
    cancel_url_name = "accounts:dashboard_users"
    form_title = "Hadia uza-na'in"
    success_message = "Uza-na'in hadia ona."
    audit_message = "Uza-na'in hadia"

    def get_queryset(self):
        qs = User.objects.all()
        if not self.request.user.is_superuser:
            qs = qs.filter(is_superuser=False)
        return qs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.is_superuser and not self.request.user.is_superuser:
            raise Http404()
        return obj


class DashboardRoleListView(DashboardBaseMixin, PermissionOrSuperuserMixin, TemplateView):
    template_name = "dashboard/roles.html"
    required_permissions = ("accounts.view_user",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        roles = list(iter_role_summaries())
        if not user.is_superuser:
            roles = [role for role in roles if role["name"] != SUPER_ADMIN]
        context["roles"] = roles
        context["can_edit_permissions"] = user.is_superuser
        context["can_manage_members"] = user_has_perm(user, "accounts.change_user")
        return context


class DashboardRoleUpdateView(DashboardBaseMixin, PermissionOrSuperuserMixin, TemplateView):
    template_name = "dashboard/role_form.html"
    required_permissions = ("accounts.view_user",)

    def dispatch(self, request, *args, **kwargs):
        role = kwargs.get("role")
        if role not in ALL_ROLES:
            raise Http404()
        if role == SUPER_ADMIN and not request.user.is_superuser:
            raise Http404()
        self.role_name = role
        self.group = get_role_group(role)
        return super().dispatch(request, *args, **kwargs)

    def _can_edit_permissions(self):
        return self.request.user.is_superuser and self.role_name != SUPER_ADMIN

    def _can_manage_members(self):
        if self.role_name == SUPER_ADMIN:
            return self.request.user.is_superuser
        return user_has_perm(self.request.user, "accounts.change_user")

    def _member_queryset(self):
        qs = self.group.user_set.all().order_by("username")
        if not self.request.user.is_superuser:
            qs = qs.filter(is_superuser=False)
        return qs

    def _candidate_queryset(self):
        qs = User.objects.filter(is_active=True).exclude(
            pk__in=self.group.user_set.values("pk")
        )
        if not self.request.user.is_superuser:
            qs = qs.filter(is_superuser=False)
        return qs.order_by("username")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        can_edit = self._can_edit_permissions()
        context["role_name"] = self.role_name
        context["role_label"] = role_label(self.role_name)
        context["role_description"] = role_description(self.role_name)
        context["locked"] = self.role_name == SUPER_ADMIN
        context["can_edit_permissions"] = can_edit
        context["can_manage_members"] = self._can_manage_members()
        context["matrix_rows"] = matrix_rows(self.group, unlocked=can_edit)
        context["members"] = self._member_queryset()
        context["candidate_users"] = self._candidate_queryset()
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "")
        if action == "save_permissions":
            return self._save_permissions(request)
        if action == "reset_defaults":
            return self._reset_defaults(request)
        if action == "add_member":
            return self._add_member(request)
        if action == "remove_member":
            return self._remove_member(request)
        messages.error(request, "Asaun la valídu.")
        return redirect(request.path)

    def _save_permissions(self, request):
        if not self._can_edit_permissions():
            raise PermissionDenied
        selected = set(request.POST.getlist("access"))
        apply_matrix_selection(self.group, selected)
        log_action(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            obj=self.group,
            message=f"Izin papél {self.role_name} hadia ona.",
            request=request,
        )
        messages.success(request, f"Izin {role_label(self.role_name)} rai ona.")
        return redirect(request.path)

    def _reset_defaults(self, request):
        if not self._can_edit_permissions():
            raise PermissionDenied
        apply_default_role_permissions(self.group)
        log_action(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            obj=self.group,
            message=f"Izin papél {self.role_name} fila ba padrão.",
            request=request,
        )
        messages.success(request, f"Izin {role_label(self.role_name)} fila ba padrão.")
        return redirect(request.path)

    def _target_user(self, request):
        user_id = request.POST.get("user_id")
        if not user_id:
            return None
        qs = User.objects.all()
        if not request.user.is_superuser:
            qs = qs.filter(is_superuser=False)
        return get_object_or_404(qs, pk=user_id)

    def _add_member(self, request):
        if not self._can_manage_members():
            raise PermissionDenied
        target = self._target_user(request)
        if target is None:
            messages.error(request, "Hili uza-na'in uluk.")
            return redirect(request.path)
        target.groups.add(self.group)
        log_action(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            obj=target,
            message=f"Uza-na'in tama ba papél {self.role_name}.",
            request=request,
        )
        messages.success(request, f"{target.get_username()} tama ona ba {role_label(self.role_name)}.")
        return redirect(request.path)

    def _remove_member(self, request):
        if not self._can_manage_members():
            raise PermissionDenied
        target = self._target_user(request)
        if target is None:
            messages.error(request, "Hili uza-na'in uluk.")
            return redirect(request.path)
        target.groups.remove(self.group)
        log_action(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            obj=target,
            message=f"Uza-na'in sai husi papél {self.role_name}.",
            request=request,
        )
        messages.success(request, f"{target.get_username()} sai ona husi {role_label(self.role_name)}.")
        return redirect(request.path)
