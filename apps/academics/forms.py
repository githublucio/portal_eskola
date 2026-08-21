from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.courses.models import Course, PublishStatus, Subject
from apps.students.models import ClassRoom, Student
from apps.teachers.models import Teacher

from .models import (
    Certificate,
    CertificateStatus,
    OnlineApplication,
    TimetableSlot,
    ApplicationSettings,
)


class OnlineApplicationForm(forms.ModelForm):
    class Meta:
        model = OnlineApplication
        fields = (
            "full_name",
            "email",
            "phone",
            "date_of_birth",
            "address",
            "desired_course",
            "desired_course_text",
            "previous_school",
            "motivation",
            "certificate_file",
        )
        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "form-control bg-white", "placeholder": "Naran kompletu"}
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control bg-white",
                    "placeholder": "email@ezemplu.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control bg-white",
                    "placeholder": "Numeru telefone",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={"class": "form-control bg-white", "type": "date"}
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control bg-white", "placeholder": "Enderesu"}
            ),
            "desired_course": forms.Select(attrs={"class": "form-select bg-white"}),
            "desired_course_text": forms.TextInput(
                attrs={"class": "form-control bg-white"}
            ),
            "previous_school": forms.TextInput(
                attrs={
                    "class": "form-control bg-white",
                    "placeholder": "Naran eskola pre-sekundária",
                }
            ),
            "motivation": forms.Textarea(
                attrs={
                    "class": "form-control bg-white",
                    "rows": 4,
                    "placeholder": "Tanbasá hakarak estuda iha ESTVP Atauro?",
                }
            ),
            "certificate_file": forms.ClearableFileInput(
                attrs={"class": "form-control bg-white", "accept": ".pdf,.jpg,.jpeg,.png"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.settings = kwargs.pop("settings", None) or ApplicationSettings.get_solo()
        super().__init__(*args, **kwargs)
        self.fields["desired_course"].queryset = Course.objects.filter(
            status=PublishStatus.PUBLISHED
        )
        self.fields["desired_course"].required = False
        self.fields["desired_course_text"].required = False
        self.fields["phone"].required = False
        self.fields["address"].required = False
        self.fields["motivation"].required = False

        self.fields["full_name"].required = True
        self.fields["email"].required = True
        self.fields["date_of_birth"].required = True
        self.fields["previous_school"].required = True
        self.fields["certificate_file"].required = True

        self.fields["full_name"].label = "Naran kompletu"
        self.fields["email"].label = "Korreiu"
        self.fields["phone"].label = "Telefone"
        self.fields["date_of_birth"].label = "Data moris"
        self.fields["address"].label = "Enderesu"
        self.fields["desired_course"].label = "Kursu hakarak"
        self.fields["desired_course_text"].label = "Kursu (hakerek)"
        self.fields["desired_course_text"].help_text = "Se kursu seidauk iha lista"
        self.fields["previous_school"].label = "Eskola pre-sekundária"
        self.fields["motivation"].label = "Motivasaun"
        self.fields["certificate_file"].label = (
            "Sertifikadu Pre-Sekundária (PDF / JPG / PNG, máximu 2MB)"
        )
        self.fields["certificate_file"].help_text = (
            "Submete sertifikadu remata eskola pre-sekundária (SMP)."
        )

    def clean_date_of_birth(self):
        born = self.cleaned_data.get("date_of_birth")
        if not born:
            raise ValidationError("Data moris obrigatóriu.")
        today = timezone.localdate()
        if born > today:
            raise ValidationError("Data moris la bele iha futuru.")
        age = today.year - born.year - (
            (today.month, today.day) < (born.month, born.day)
        )
        min_age = self.settings.min_age
        max_age = self.settings.max_age
        if age < min_age:
            raise ValidationError(
                f"Kandidatu nia idade tenke mínimu {min_age} tinan."
            )
        if age > max_age:
            raise ValidationError(
                f"Kandidatu nia idade labele liu {max_age} tinan."
            )
        return born

    def clean(self):
        if not self.settings.is_accepting:
            raise ValidationError(
                self.settings.closed_message
                or "Kandidatura online taka ona."
            )
        cleaned = super().clean()
        course = cleaned.get("desired_course")
        course_text = (cleaned.get("desired_course_text") or "").strip()
        if not course and not course_text:
            raise ValidationError(
                "Hili kursu husi lista ka hakerek naran kursu iha kampu 'Kursu (hakerek)'."
            )
        return cleaned


class _BootstrapFormMixin:
    def _style_fields(self):
        for field in self.fields.values():
            name = field.widget.__class__.__name__
            if name == "CheckboxInput":
                field.widget.attrs.setdefault("class", "form-check-input")
            elif name in {"Select", "SelectMultiple", "NullBooleanSelect"}:
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class AttendanceFilterForm(forms.Form, _BootstrapFormMixin):
    classroom = forms.ModelChoiceField(queryset=ClassRoom.objects.none(), label="Turma")
    subject = forms.ModelChoiceField(queryset=Subject.objects.none(), label="Disiplina")
    date = forms.DateField(
        label="Data",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, classrooms=None, subjects=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["classroom"].queryset = classrooms or ClassRoom.objects.none()
        self.fields["subject"].queryset = subjects or Subject.objects.none()
        self._style_fields()


class GradeRosterForm(forms.Form, _BootstrapFormMixin):
    classroom = forms.ModelChoiceField(queryset=ClassRoom.objects.none(), label="Turma")
    subject = forms.ModelChoiceField(queryset=Subject.objects.none(), label="Disiplina")
    term = forms.IntegerField(min_value=1, max_value=4, initial=1, label="Períodu")
    assessment_name = forms.CharField(
        max_length=120, required=False, label="Avaliasaun"
    )
    max_score = forms.DecimalField(
        max_digits=5, decimal_places=2, initial=100, min_value=1, label="Nota máximu"
    )

    def __init__(self, *args, classrooms=None, subjects=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["classroom"].queryset = classrooms or ClassRoom.objects.none()
        self.fields["subject"].queryset = subjects or Subject.objects.none()
        self._style_fields()


class TimetableSlotForm(forms.ModelForm, _BootstrapFormMixin):
    class Meta:
        model = TimetableSlot
        fields = (
            "classroom",
            "subject",
            "teacher",
            "weekday",
            "start_time",
            "end_time",
            "room",
            "is_active",
        )
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["classroom"].queryset = ClassRoom.objects.filter(
            is_active=True
        ).select_related("course", "academic_year")
        self.fields["subject"].queryset = Subject.objects.filter(is_active=True)
        self.fields["teacher"].queryset = Teacher.objects.filter(status="active")
        self.fields["teacher"].required = False
        self.fields["classroom"].label = "Turma"
        self.fields["subject"].label = "Disiplina"
        self.fields["teacher"].label = "Profesór"
        self.fields["weekday"].label = "Loron"
        self.fields["start_time"].label = "Oras hahú"
        self.fields["end_time"].label = "Oras remata"
        self.fields["room"].label = "Sala"
        self.fields["is_active"].label = "Ativu"
        self._style_fields()

    def clean(self):
        cleaned = super().clean()
        classroom = cleaned.get("classroom")
        subject = cleaned.get("subject")
        if classroom and subject and subject.course_id != classroom.course_id:
            raise ValidationError(
                {"subject": "Disiplina tenke halo parte iha kursu turma nian."}
            )
        return cleaned


class CertificateIssueForm(forms.ModelForm, _BootstrapFormMixin):
    class Meta:
        model = Certificate
        fields = (
            "student",
            "title",
            "certificate_number",
            "academic_year",
            "status",
            "notes",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.all()
        self.fields["certificate_number"].required = False
        self.fields["student"].label = "Estudante"
        self.fields["title"].label = "Títulu"
        self.fields["certificate_number"].label = "Númeru sertifikadu"
        self.fields["certificate_number"].help_text = "Mamuk = númeru automátiku"
        self.fields["academic_year"].label = "Tinan akadémiku"
        self.fields["status"].label = "Estadu"
        self.fields["notes"].label = "Nota"
        self.fields["status"].initial = CertificateStatus.ISSUED
        self._style_fields()


class NotificationComposeForm(forms.Form, _BootstrapFormMixin):
    AUDIENCE_CHOICES = (
        ("students", "Estudante sira ho konta"),
        ("teachers", "Profesór sira ho konta"),
        ("staff", "Estafe / administrasaun"),
        ("all", "Uza-na'in ativu hotu"),
    )
    title = forms.CharField(max_length=200, label="Títulu")
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), label="Mensajen")
    link = forms.CharField(max_length=255, required=False, label="Ligasaun (opsionál)")
    audience = forms.ChoiceField(choices=AUDIENCE_CHOICES, label="Simu-na'in sira")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()
