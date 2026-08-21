from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView

from apps.accounts.audit import log_action
from apps.accounts.models import AuditLog
from apps.courses.models import Subject
from apps.students.models import ClassRoom, StudentClass, StudentClassStatus

from .forms import AttendanceFilterForm, GradeRosterForm, OnlineApplicationForm
from .mixins import StudentPortalMixin, TeacherPortalMixin
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
)
from .services import (
    active_students_for_classroom,
    classrooms_for_teacher,
    save_attendance_roster,
    save_grade_roster,
    subjects_for_teacher_classroom,
    teacher_can_access_classroom,
)


class ApplyCreateView(CreateView):
    model = OnlineApplication
    form_class = OnlineApplicationForm
    template_name = "academics/apply.html"
    success_url = reverse_lazy("academics:apply_thanks")

    def dispatch(self, request, *args, **kwargs):
        self.app_settings = ApplicationSettings.get_solo()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["settings"] = self.app_settings
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_settings"] = self.app_settings
        context["criteria"] = ApplicationCriterion.objects.filter(is_active=True)
        context["applications_open"] = self.app_settings.is_accepting
        return context

    def post(self, request, *args, **kwargs):
        if not self.app_settings.is_accepting:
            messages.error(
                request,
                self.app_settings.closed_message
                or "Kandidatura online taka ona.",
            )
            return redirect("academics:apply")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(
            self.request,
            "Kandidatura haruka ona. Ekipa eskola sei kontakta ita.",
        )
        return super().form_valid(form)


class ApplyThanksView(TemplateView):
    template_name = "academics/apply_thanks.html"


class StudentPortalHomeView(StudentPortalMixin, TemplateView):
    template_name = "academics/portal/student_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_student()
        context["student"] = student
        context["current_class"] = student.current_class()
        context["recent_grades"] = GradeEntry.objects.filter(
            student=student
        ).select_related("subject", "academic_year")[:5]
        context["recent_attendance"] = AttendanceRecord.objects.filter(
            student=student
        ).select_related("subject", "classroom")[:8]
        context["certificates"] = Certificate.objects.filter(
            student=student, status=CertificateStatus.ISSUED
        )[:5]
        context["unread_notifications"] = Notification.objects.filter(
            user=self.request.user, is_read=False
        )[:5]
        return context


class StudentGradesView(StudentPortalMixin, ListView):
    template_name = "academics/portal/student_grades.html"
    context_object_name = "grades"
    paginate_by = 30

    def get_queryset(self):
        return (
            GradeEntry.objects.filter(student=self.get_student())
            .select_related("subject", "classroom", "academic_year")
            .order_by("-academic_year__start_date", "term", "subject__code")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["student"] = self.get_student()
        return context


class StudentAttendanceView(StudentPortalMixin, ListView):
    template_name = "academics/portal/student_attendance.html"
    context_object_name = "records"
    paginate_by = 40

    def get_queryset(self):
        return (
            AttendanceRecord.objects.filter(student=self.get_student())
            .select_related("subject", "classroom")
            .order_by("-date")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_student()
        context["student"] = student
        stats = (
            AttendanceRecord.objects.filter(student=student)
            .values("status")
            .annotate(total=Count("id"))
        )
        context["attendance_stats"] = {row["status"]: row["total"] for row in stats}
        return context


class StudentTimetableView(StudentPortalMixin, TemplateView):
    template_name = "academics/portal/student_timetable.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_student()
        context["student"] = student
        assignment = student.current_class()
        slots = TimetableSlot.objects.none()
        if assignment:
            slots = (
                TimetableSlot.objects.filter(
                    classroom=assignment.classroom, is_active=True
                )
                .select_related("subject", "teacher")
                .order_by("weekday", "start_time")
            )
        context["slots"] = slots
        context["assignment"] = assignment
        return context


class StudentCertificatesView(StudentPortalMixin, ListView):
    template_name = "academics/portal/student_certificates.html"
    context_object_name = "certificates"

    def get_queryset(self):
        return Certificate.objects.filter(
            student=self.get_student(),
            status=CertificateStatus.ISSUED,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["student"] = self.get_student()
        return context


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = "academics/portal/notifications.html"
    context_object_name = "notifications"
    paginate_by = 30

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
        return super().get(request, *args, **kwargs)


class TeacherPortalHomeView(TeacherPortalMixin, TemplateView):
    template_name = "academics/portal/teacher_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_teacher()
        context["teacher"] = teacher
        context["advised_classes"] = teacher.advised_classes.filter(is_active=True)
        context["today_slots"] = (
            TimetableSlot.objects.filter(
                teacher=teacher,
                is_active=True,
                weekday=timezone.localdate().isoweekday(),
            )
            .select_related("classroom", "subject")
            .order_by("start_time")
        )
        context["recent_grades"] = GradeEntry.objects.filter(
            recorded_by=teacher
        ).select_related("student", "subject")[:8]
        return context


class TeacherTimetableView(TeacherPortalMixin, ListView):
    template_name = "academics/portal/teacher_timetable.html"
    context_object_name = "slots"

    def get_queryset(self):
        return (
            TimetableSlot.objects.filter(teacher=self.get_teacher(), is_active=True)
            .select_related("classroom", "subject")
            .order_by("weekday", "start_time")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["teacher"] = self.get_teacher()
        return context


class TeacherClassListView(TeacherPortalMixin, TemplateView):
    template_name = "academics/portal/teacher_classes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_teacher()
        context["teacher"] = teacher
        context["advised_classes"] = teacher.advised_classes.filter(
            is_active=True
        ).select_related("course", "academic_year")
        context["teaching_classes"] = (
            TimetableSlot.objects.filter(teacher=teacher, is_active=True)
            .values(
                "classroom_id",
                "classroom__name",
                "classroom__course__code",
                "classroom__academic_year__name",
            )
            .annotate(slots=Count("id"))
            .order_by("classroom__name")
        )
        return context


class TeacherClassStudentsView(TeacherPortalMixin, TemplateView):
    template_name = "academics/portal/teacher_class_students.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_teacher()
        classroom = get_object_or_404(ClassRoom, pk=self.kwargs["classroom_id"])
        allowed = classroom.adviser_id == teacher.pk or TimetableSlot.objects.filter(
            teacher=teacher, classroom=classroom, is_active=True
        ).exists()
        if not allowed:
            raise PermissionDenied
        context["teacher"] = teacher
        context["classroom"] = classroom
        context["assignments"] = (
            StudentClass.objects.filter(
                classroom=classroom, status=StudentClassStatus.ACTIVE
            )
            .select_related("student")
            .order_by("student__last_name", "student__first_name")
        )
        context["avg_score"] = GradeEntry.objects.filter(classroom=classroom).aggregate(
            avg_score=Avg("score")
        )["avg_score"]
        return context


class TeacherAttendanceSummaryView(TeacherPortalMixin, TemplateView):
    template_name = "academics/portal/teacher_attendance_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_teacher()
        context["teacher"] = teacher
        classrooms = classrooms_for_teacher(teacher)
        context["summary"] = (
            AttendanceRecord.objects.filter(classroom__in=classrooms)
            .values("classroom__name", "status")
            .annotate(total=Count("id"))
            .order_by("classroom__name")
        )
        return context


class TeacherAttendanceMarkView(TeacherPortalMixin, TemplateView):
    template_name = "academics/portal/teacher_attendance_mark.html"

    def _classrooms(self):
        return classrooms_for_teacher(self.get_teacher())

    def _subjects(self, classroom=None):
        teacher = self.get_teacher()
        if classroom:
            return subjects_for_teacher_classroom(teacher, classroom)
        subject_ids = TimetableSlot.objects.filter(
            teacher=teacher, is_active=True
        ).values_list("subject_id", flat=True)
        advised_courses = teacher.advised_classes.filter(is_active=True).values_list(
            "course_id", flat=True
        )
        return Subject.objects.filter(
            Q(pk__in=subject_ids) | Q(course_id__in=advised_courses),
            is_active=True,
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_teacher()
        context["teacher"] = teacher
        classrooms = self._classrooms()
        classroom = None
        classroom_id = self.request.GET.get("classroom") or self.request.POST.get(
            "classroom"
        )
        if classroom_id:
            classroom = classrooms.filter(pk=classroom_id).first()
        subjects = self._subjects(classroom)
        initial = {
            "date": timezone.localdate(),
        }
        if classroom:
            initial["classroom"] = classroom
        subject_id = self.request.GET.get("subject") or self.request.POST.get("subject")
        if subject_id:
            initial["subject"] = subject_id
        if self.request.GET.get("date"):
            initial["date"] = self.request.GET.get("date")
        form = AttendanceFilterForm(
            self.request.POST or self.request.GET or None,
            classrooms=classrooms,
            subjects=subjects,
            initial=initial,
        )
        if not self.request.POST and not self.request.GET.get("classroom"):
            form = AttendanceFilterForm(
                classrooms=classrooms, subjects=subjects, initial=initial
            )
        context["form"] = form
        context["roster"] = []
        context["status_choices"] = AttendanceStatus.choices
        if classroom and form.is_valid():
            subject = form.cleaned_data["subject"]
            date = form.cleaned_data["date"]
            if subject not in subjects:
                raise PermissionDenied
            existing = {
                row.student_id: row.status
                for row in AttendanceRecord.objects.filter(
                    classroom=classroom, subject=subject, date=date
                )
            }
            context["roster"] = [
                {
                    "student": assignment.student,
                    "status": existing.get(
                        assignment.student_id, AttendanceStatus.PRESENT
                    ),
                }
                for assignment in active_students_for_classroom(classroom)
            ]
            context["selected_classroom"] = classroom
            context["selected_subject"] = subject
            context["selected_date"] = date
        return context

    def post(self, request, *args, **kwargs):
        teacher = self.get_teacher()
        classroom = ClassRoom.objects.filter(pk=request.POST.get("classroom")).first()
        if classroom and not teacher_can_access_classroom(teacher, classroom):
            raise PermissionDenied
        classrooms = self._classrooms()
        form = AttendanceFilterForm(
            request.POST,
            classrooms=classrooms,
            subjects=self._subjects(classroom),
        )
        if not form.is_valid():
            return self.get(request, *args, **kwargs)
        classroom = form.cleaned_data["classroom"]
        subject = form.cleaned_data["subject"]
        date = form.cleaned_data["date"]
        if subject not in self._subjects(classroom):
            raise PermissionDenied
        statuses = {
            key.replace("status_", ""): value
            for key, value in request.POST.items()
            if key.startswith("status_")
        }
        saved = save_attendance_roster(
            classroom=classroom,
            subject=subject,
            date=date,
            teacher=teacher,
            statuses=statuses,
        )
        log_action(
            user=request.user,
            action=AuditLog.Action.CREATE,
            message=f"Asisténsia {classroom} / {subject} / {date} ({saved})",
            request=request,
            object_type="AttendanceRecord",
        )
        messages.success(request, f"Asisténsia rai ona ({saved} estudante).")
        return redirect(
            f"{reverse('academics:teacher_attendance_mark')}"
            f"?classroom={classroom.pk}&subject={subject.pk}&date={date.isoformat()}"
        )


class TeacherGradeEntryView(TeacherPortalMixin, TemplateView):
    template_name = "academics/portal/teacher_grades_entry.html"

    def _classrooms(self):
        return classrooms_for_teacher(self.get_teacher())

    def _subjects(self, classroom=None):
        teacher = self.get_teacher()
        if classroom:
            return subjects_for_teacher_classroom(teacher, classroom)
        return Subject.objects.filter(
            course_id__in=self._classrooms().values("course_id"), is_active=True
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_teacher()
        context["teacher"] = teacher
        classrooms = self._classrooms()
        classroom_id = self.request.GET.get("classroom") or self.request.POST.get(
            "classroom"
        )
        classroom = classrooms.filter(pk=classroom_id).first() if classroom_id else None
        subjects = self._subjects(classroom)
        data = self.request.POST or self.request.GET or None
        form = GradeRosterForm(data, classrooms=classrooms, subjects=subjects)
        if not data:
            form = GradeRosterForm(classrooms=classrooms, subjects=subjects)
        context["form"] = form
        context["roster"] = []
        if classroom and (self.request.GET.get("subject") or self.request.POST):
            bound = GradeRosterForm(
                self.request.GET or self.request.POST,
                classrooms=classrooms,
                subjects=subjects,
            )
            if bound.is_valid():
                subject = bound.cleaned_data["subject"]
                term = bound.cleaned_data["term"]
                assessment = bound.cleaned_data.get("assessment_name") or ""
                context["form"] = bound
                existing = {
                    row.student_id: row
                    for row in GradeEntry.objects.filter(
                        classroom=classroom,
                        subject=subject,
                        academic_year=classroom.academic_year,
                        term=term,
                        assessment_name=assessment,
                    )
                }
                context["roster"] = [
                    {
                        "student": assignment.student,
                        "score": existing[assignment.student_id].score
                        if assignment.student_id in existing
                        else "",
                    }
                    for assignment in active_students_for_classroom(classroom)
                ]
                context["selected_classroom"] = classroom
        return context

    def post(self, request, *args, **kwargs):
        teacher = self.get_teacher()
        classroom = ClassRoom.objects.filter(pk=request.POST.get("classroom")).first()
        if classroom and not teacher_can_access_classroom(teacher, classroom):
            raise PermissionDenied
        classrooms = self._classrooms()
        form = GradeRosterForm(
            request.POST,
            classrooms=classrooms,
            subjects=self._subjects(classroom),
        )
        if not form.is_valid():
            return self.get(request, *args, **kwargs)
        classroom = form.cleaned_data["classroom"]
        subject = form.cleaned_data["subject"]
        if subject not in self._subjects(classroom):
            raise PermissionDenied
        scores = {
            key.replace("score_", ""): value
            for key, value in request.POST.items()
            if key.startswith("score_")
        }
        saved = save_grade_roster(
            classroom=classroom,
            subject=subject,
            academic_year=classroom.academic_year,
            term=form.cleaned_data["term"],
            assessment_name=form.cleaned_data.get("assessment_name") or "",
            teacher=teacher,
            scores=scores,
            max_score=form.cleaned_data["max_score"],
        )
        log_action(
            user=request.user,
            action=AuditLog.Action.CREATE,
            message=f"Nota {classroom} / {subject} T{form.cleaned_data['term']} ({saved})",
            request=request,
            object_type="GradeEntry",
        )
        messages.success(request, f"Nota sira rai ona ({saved} estudante).")
        query = (
            f"?classroom={classroom.pk}&subject={subject.pk}"
            f"&term={form.cleaned_data['term']}"
            f"&assessment_name={form.cleaned_data.get('assessment_name') or ''}"
            f"&max_score={form.cleaned_data['max_score']}"
        )
        return redirect(reverse("academics:teacher_grades_entry") + query)
