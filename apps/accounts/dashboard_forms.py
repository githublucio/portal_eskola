from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.utils import timezone

from apps.academics.models import (
    ApplicationCriterion,
    ApplicationSettings,
    OnlineApplication,
)
from apps.core.validators import validate_image_file
from apps.courses.models import Course, Subject
from apps.documents.models import Document, DocumentCategory
from apps.events.models import Event
from apps.gallery.models import GalleryAlbum, GalleryPhoto
from apps.news.models import News, NewsCategory
from apps.students.models import Student
from apps.teachers.models import Teacher

from .forms import DashboardUserChangeForm
from .models import User
from .roles import SUPER_ADMIN


class DashboardModelForm(forms.ModelForm):
    publish_permission = ""

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self._style_fields()
        self._restrict_publish()

    def _style_fields(self):
        for name, field in self.fields.items():
            widget_name = field.widget.__class__.__name__
            if widget_name == "CheckboxInput":
                field.widget.attrs.setdefault("class", "form-check-input")
            elif widget_name == "CheckboxSelectMultiple":
                field.widget.attrs.setdefault("class", "form-check-input")
            elif widget_name in {"Select", "SelectMultiple", "NullBooleanSelect"}:
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def _restrict_publish(self):
        if "status" not in self.fields or not self.publish_permission:
            return
        user = self.user
        if not user or user.is_superuser or user.has_perm(self.publish_permission):
            return
        current = getattr(self.instance, "status", None) if self.instance.pk else None
        allowed = [choice for choice in self.fields["status"].choices if choice[0] != "published"]
        if current == "published":
            published = next(
                (choice for choice in self.fields["status"].choices if choice[0] == "published"),
                None,
            )
            if published:
                allowed = [published, *allowed]
        self.fields["status"].choices = allowed

    def clean_status(self):
        status = self.cleaned_data.get("status")
        if status != "published" or not self.publish_permission:
            return status
        user = self.user
        current = getattr(self.instance, "status", None) if self.instance.pk else None
        if current == "published":
            return status
        if user and (user.is_superuser or user.has_perm(self.publish_permission)):
            return status
        raise forms.ValidationError("Ita la iha permissaun atu publika.")


def _datetime_widget():
    return forms.DateTimeInput(
        attrs={"type": "datetime-local"},
        format="%Y-%m-%dT%H:%M",
    )


class NewsForm(DashboardModelForm):
    publish_permission = "news.publish_news"

    class Meta:
        model = News
        fields = (
            "title",
            "category",
            "summary",
            "content",
            "featured_image",
            "status",
            "is_announcement",
        )
        labels = {
            "title": "Títulu",
            "category": "Kategoria",
            "summary": "Rezumu",
            "content": "Konteúdu",
            "featured_image": "Imajen",
            "status": "Estadu",
            "is_announcement": "Avisu importante",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        image = self.fields["featured_image"]
        image.required = False
        image.validators = list(image.validators) + list(validate_image_file)


class NewsCategoryForm(DashboardModelForm):
    class Meta:
        model = NewsCategory
        fields = ("name",)
        labels = {"name": "Naran"}


class EventForm(DashboardModelForm):
    publish_permission = "events.publish_event"

    class Meta:
        model = Event
        fields = (
            "title",
            "description",
            "location",
            "organizer",
            "start_at",
            "end_at",
            "image",
            "status",
        )
        labels = {
            "title": "Títulu",
            "description": "Deskrisaun",
            "location": "Fatin",
            "organizer": "Organizadór",
            "start_at": "Hahú",
            "end_at": "Remata",
            "image": "Imajen",
            "status": "Estadu",
        }
        widgets = {
            "start_at": _datetime_widget(),
            "end_at": _datetime_widget(),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("start_at", "end_at"):
            self.fields[name].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"]
            value = getattr(self.instance, name, None)
            if value:
                self.initial[name] = timezone.localtime(value).strftime("%Y-%m-%dT%H:%M")


class DocumentForm(DashboardModelForm):
    publish_permission = "documents.publish_document"

    class Meta:
        model = Document
        fields = (
            "title",
            "category",
            "description",
            "file",
            "version",
            "is_public",
            "status",
        )
        labels = {
            "title": "Títulu",
            "category": "Kategoria",
            "description": "Deskrisaun",
            "file": "Arkivu",
            "version": "Versaun",
            "is_public": "Públiku",
            "status": "Estadu",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].empty_label = "Hili kategoria…"
        if not DocumentCategory.objects.exists():
            self.fields["category"].help_text = (
                "Seidauk iha kategoria. Kria uluk iha "
                "Dashboard → Dokumentu sira → Kategoria "
                "(ka /dashboard/documents/categories/new/)."
            )
        else:
            self.fields["category"].help_text = (
                "Kategoria tenke iha. Bele kria foun iha "
                "/dashboard/documents/categories/new/"
            )


class DocumentCategoryForm(DashboardModelForm):
    class Meta:
        model = DocumentCategory
        fields = ("name",)
        labels = {"name": "Naran"}


class GalleryAlbumForm(DashboardModelForm):
    publish_permission = "gallery.publish_galleryalbum"

    class Meta:
        model = GalleryAlbum
        fields = ("title", "description", "cover_image", "event", "status")
        labels = {
            "title": "Títulu",
            "description": "Deskrisaun",
            "cover_image": "Imajen kapa",
            "event": "Eventu",
            "status": "Estadu",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["event"].required = False
        self.fields["cover_image"].help_text = (
            "Uza imajen landscape nia rezolusaun aas (ladu 1600px) atu mosu klean iha slide hero. "
            "Se álbum seidauk iha foto, kapa ne'e sei sai foto dahuluk."
        )

    def save(self, commit=True):
        album = super().save(commit=commit)
        if commit:
            album.ensure_cover_photo()
        return album


class GalleryPhotoForm(DashboardModelForm):
    class Meta:
        model = GalleryPhoto
        fields = ("image", "caption", "sort_order")
        labels = {
            "image": "Imajen",
            "caption": "Legenda",
            "sort_order": "Orden",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].help_text = (
            "Uza foto nia rezolusaun aas no formatu landscape (16:9). "
            "Imajen ki'ik ka burak sei mosu la klean iha slide hero."
        )


class CourseForm(DashboardModelForm):
    publish_permission = "courses.publish_course"

    class Meta:
        model = Course
        fields = (
            "department",
            "code",
            "name",
            "description",
            "duration",
            "qualification",
            "requirements",
            "image",
            "status",
        )
        labels = {
            "department": "Departamentu",
            "code": "Kódigu",
            "name": "Naran",
            "description": "Deskrisaun",
            "duration": "Durasaun",
            "qualification": "Kualifikasaun",
            "requirements": "Rekizitu",
            "image": "Imajen",
            "status": "Estadu",
        }


class SubjectForm(DashboardModelForm):
    class Meta:
        model = Subject
        fields = ("code", "name", "description", "credits", "semester", "is_active")
        labels = {
            "code": "Kódigu",
            "name": "Naran",
            "description": "Deskrisaun",
            "credits": "Kréditu",
            "semester": "Períodu",
            "is_active": "Ativu",
        }


class StudentForm(DashboardModelForm):
    class Meta:
        model = Student
        fields = (
            "student_number",
            "first_name",
            "last_name",
            "email",
            "phone",
            "date_of_birth",
            "gender",
            "address",
            "guardian_name",
            "guardian_phone",
            "photo",
            "status",
            "notes",
            "user",
        )
        labels = {
            "student_number": "Númeru estudante",
            "first_name": "Naran uluk",
            "last_name": "Naran ikus",
            "email": "Korreiu",
            "phone": "Telefone",
            "date_of_birth": "Data moris",
            "gender": "Jéneru",
            "address": "Enderesu",
            "guardian_name": "Naran encarregado",
            "guardian_phone": "Telefone encarregado",
            "photo": "Foto",
            "status": "Estadu",
            "notes": "Nota",
            "user": "Uza-na'in",
        }
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].required = False
        qs = User.objects.filter(student_profile__isnull=True).order_by("username")
        if self.instance.pk and self.instance.user_id:
            qs = User.objects.filter(pk=self.instance.user_id) | qs
        if self.user and not self.user.is_superuser:
            qs = qs.filter(is_superuser=False)
        self.fields["user"].queryset = qs.distinct()


class TeacherForm(DashboardModelForm):
    class Meta:
        model = Teacher
        fields = (
            "employee_number",
            "first_name",
            "last_name",
            "email",
            "phone",
            "department",
            "specialization",
            "qualification",
            "bio",
            "photo",
            "status",
            "hire_date",
            "user",
        )
        labels = {
            "employee_number": "Númeru profesór",
            "first_name": "Naran uluk",
            "last_name": "Naran ikus",
            "email": "Korreiu",
            "phone": "Telefone",
            "department": "Departamentu",
            "specialization": "Espesializasaun",
            "qualification": "Kualifikasaun",
            "bio": "Biografia",
            "photo": "Foto",
            "status": "Estadu",
            "hire_date": "Data tama",
            "user": "Uza-na'in",
        }
        widgets = {
            "hire_date": forms.DateInput(attrs={"type": "date"}),
            "bio": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].required = False
        qs = User.objects.filter(teacher_profile__isnull=True).order_by("username")
        if self.instance.pk and self.instance.user_id:
            qs = User.objects.filter(pk=self.instance.user_id) | qs
        if self.user and not self.user.is_superuser:
            qs = qs.filter(is_superuser=False)
        self.fields["user"].queryset = qs.distinct()


class ApplicationStatusForm(DashboardModelForm):
    class Meta:
        model = OnlineApplication
        fields = ("status", "staff_notes")
        labels = {
            "status": "Estadu",
            "staff_notes": "Nota estafe",
        }
        widgets = {
            "staff_notes": forms.Textarea(attrs={"rows": 3}),
        }


class ApplicationSettingsForm(DashboardModelForm):
    class Meta:
        model = ApplicationSettings
        fields = (
            "is_open",
            "title",
            "intro",
            "closed_message",
            "min_age",
            "max_age",
            "opens_at",
            "closes_at",
        )
        labels = {
            "is_open": "Formuláriu aktivu (simu kandidatura)",
            "title": "Títulu pájina",
            "intro": "Introdusaun",
            "closed_message": "Mensajen bainhira taka",
            "min_age": "Idade mínimu",
            "max_age": "Idade máximu",
            "opens_at": "Hahú (opsionál)",
            "closes_at": "Remata (opsionál)",
        }
        widgets = {
            "intro": forms.Textarea(attrs={"rows": 3}),
            "closed_message": forms.Textarea(attrs={"rows": 3}),
            "opens_at": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local"},
            ),
            "closes_at": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local"},
            ),
        }
        help_texts = {
            "is_open": "Desmarca atu taka formuláriu depois pendaftaran remata.",
            "opens_at": "Se preenche, kandidatura mosu de'it depois data/oras ne'e.",
            "closes_at": "Se preenche, kandidatura taka automaticamente depois data/oras ne'e.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("opens_at", "closes_at"):
            self.fields[name].required = False
            self.fields[name].input_formats = [
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
            ]

    def clean(self):
        cleaned = super().clean()
        min_age = cleaned.get("min_age")
        max_age = cleaned.get("max_age")
        if min_age is not None and max_age is not None and min_age > max_age:
            raise forms.ValidationError("Idade mínimu labele boot liu idade máximu.")
        opens_at = cleaned.get("opens_at")
        closes_at = cleaned.get("closes_at")
        if opens_at and closes_at and opens_at >= closes_at:
            raise forms.ValidationError("Data hahú tenke molok data remata.")
        return cleaned


class ApplicationCriterionForm(DashboardModelForm):
    class Meta:
        model = ApplicationCriterion
        fields = ("text", "sort_order", "is_active")
        labels = {
            "text": "Tekstu kritériu",
            "sort_order": "Orden",
            "is_active": "Ativu (hatudu iha formuláriu)",
        }
        widgets = {
            "text": forms.Textarea(attrs={"rows": 2}),
        }


class DashboardUserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username",
            "display_name",
            "first_name",
            "last_name",
            "email",
            "phone",
            "is_active",
            "is_staff",
            "groups",
        )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        labels = {
            "username": "Naran uza-na'in",
            "display_name": "Naran hatudu",
            "first_name": "Naran uluk",
            "last_name": "Naran ikus",
            "email": "Korreiu",
            "phone": "Telefone",
            "is_active": "Ativu",
            "is_staff": "Estafe",
            "groups": "Grupu / papél",
            "password1": "Liafuan-sekrétu",
            "password2": "Konfirma liafuan-sekrétu",
        }
        self.fields["groups"].required = False
        self.fields["groups"].widget = forms.CheckboxSelectMultiple()
        self.fields["groups"].queryset = self._group_queryset()
        for name, field in self.fields.items():
            field.help_text = ""
            if name in labels:
                field.label = labels[name]
            widget_name = field.widget.__class__.__name__
            if widget_name == "CheckboxInput":
                field.widget.attrs.setdefault("class", "form-check-input")
            elif widget_name == "CheckboxSelectMultiple":
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                field.widget.attrs.setdefault("class", "form-control")
        self.fields["groups"].help_text = "Hili papél atu fó asesu. Super admin bele hadia izin iha Papél no asesu."

    def _group_queryset(self):
        qs = Group.objects.all().order_by("name")
        if not self.user or not self.user.is_superuser:
            qs = qs.exclude(name=SUPER_ADMIN)
        return qs


class StyledDashboardUserChangeForm(DashboardUserChangeForm):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        labels = {
            "username": "Naran uza-na'in",
            "display_name": "Naran hatudu",
            "first_name": "Naran uluk",
            "last_name": "Naran ikus",
            "email": "Korreiu",
            "phone": "Telefone",
            "is_active": "Ativu",
            "groups": "Grupu / papél",
        }
        self.fields["groups"].required = False
        self.fields["groups"].widget = forms.CheckboxSelectMultiple()
        qs = Group.objects.all().order_by("name")
        if not self.user or not self.user.is_superuser:
            qs = qs.exclude(name=SUPER_ADMIN)
        self.fields["groups"].queryset = qs
        for name, field in self.fields.items():
            field.help_text = ""
            if name in labels:
                field.label = labels[name]
            widget_name = field.widget.__class__.__name__
            if widget_name == "CheckboxInput":
                field.widget.attrs.setdefault("class", "form-check-input")
            elif widget_name == "CheckboxSelectMultiple":
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                field.widget.attrs.setdefault("class", "form-control")
        self.fields["groups"].help_text = "Hili papél atu fó asesu. Super admin bele hadia izin iha Papél no asesu."
