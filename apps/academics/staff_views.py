from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, ListView, TemplateView, View

from apps.accounts.audit import log_action
from apps.accounts.mixins import DashboardBaseMixin, PermissionOrSuperuserMixin
from apps.accounts.models import AuditLog
from apps.students.models import ClassRoom

from .forms import CertificateIssueForm, NotificationComposeForm, TimetableSlotForm
from .models import Certificate, CertificateStatus, TimetableSlot
from .services import next_certificate_number, send_notifications


class StaffSectionMixin(DashboardBaseMixin, PermissionOrSuperuserMixin):
    pass


class DashboardTimetableListView(StaffSectionMixin, ListView):
    model = TimetableSlot
    template_name = "dashboard/timetable_list.html"
    context_object_name = "slots"
    paginate_by = 30
    required_permissions = ("academics.view_timetableslot",)
    ordering = ("weekday", "start_time")

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("classroom", "subject", "teacher")
        )
        classroom_id = self.request.GET.get("classroom")
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["classrooms"] = ClassRoom.objects.filter(is_active=True)
        context["selected_classroom"] = self.request.GET.get("classroom", "")
        context["can_add"] = self.request.user.is_superuser or self.request.user.has_perm(
            "academics.add_timetableslot"
        )
        return context


class DashboardTimetableCreateView(StaffSectionMixin, CreateView):
    model = TimetableSlot
    form_class = TimetableSlotForm
    template_name = "dashboard/timetable_form.html"
    success_url = reverse_lazy("academics:dashboard_timetable")
    required_permissions = ("academics.add_timetableslot",)

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            obj=self.object,
            message="Oráriu kria",
            request=self.request,
        )
        messages.success(self.request, "Slot oráriu kria ona.")
        return response


class DashboardTimetableDeleteView(StaffSectionMixin, View):
    required_permissions = ("academics.change_timetableslot",)

    def post(self, request, pk):
        slot = get_object_or_404(TimetableSlot, pk=pk)
        log_action(
            user=request.user,
            action=AuditLog.Action.DELETE,
            obj=slot,
            message="Oráriu hasai",
            request=request,
        )
        slot.delete()
        messages.success(request, "Slot oráriu hasai ona.")
        return redirect("academics:dashboard_timetable")


class DashboardCertificateListView(StaffSectionMixin, ListView):
    model = Certificate
    template_name = "dashboard/certificate_list.html"
    context_object_name = "certificates"
    paginate_by = 25
    required_permissions = ("academics.view_certificate",)
    ordering = ("-created_at",)

    def get_queryset(self):
        return super().get_queryset().select_related("student", "academic_year")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_add"] = self.request.user.is_superuser or self.request.user.has_perm(
            "academics.add_certificate"
        )
        return context


class DashboardCertificateCreateView(StaffSectionMixin, CreateView):
    model = Certificate
    form_class = CertificateIssueForm
    template_name = "dashboard/certificate_form.html"
    success_url = reverse_lazy("academics:dashboard_certificates")
    required_permissions = ("academics.add_certificate",)

    def form_valid(self, form):
        cert = form.save(commit=False)
        if not cert.certificate_number:
            cert.certificate_number = next_certificate_number()
        cert.issued_by = self.request.user
        cert.save()
        self.object = cert
        log_action(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            obj=cert,
            message=f"Sertifikadu {cert.certificate_number}",
            request=self.request,
        )
        messages.success(self.request, "Sertifikadu rai ona.")
        return redirect(self.success_url)


class CertificatePrintView(LoginRequiredMixin, TemplateView):
    template_name = "academics/certificate_print.html"

    def get_certificate(self):
        cert = get_object_or_404(
            Certificate.objects.select_related("student", "academic_year", "issued_by"),
            pk=self.kwargs["pk"],
        )
        user = self.request.user
        if user.is_superuser or user.has_perm("academics.view_certificate"):
            return cert
        if (
            hasattr(user, "student_profile")
            and cert.student_id == user.student_profile.pk
            and cert.status == CertificateStatus.ISSUED
        ):
            return cert
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["certificate"] = self.get_certificate()
        return context


class DashboardNotificationComposeView(StaffSectionMixin, FormView):
    form_class = NotificationComposeForm
    template_name = "dashboard/notification_form.html"
    success_url = reverse_lazy("academics:dashboard_notifications")
    required_permissions = ("academics.add_notification",)

    def form_valid(self, form):
        count = send_notifications(
            title=form.cleaned_data["title"],
            message=form.cleaned_data["message"],
            link=form.cleaned_data.get("link") or "",
            audience=form.cleaned_data["audience"],
            created_by=self.request.user,
        )
        log_action(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            message=f"Notifikasaun haruka ba uza-na'in {count}",
            request=self.request,
            object_type="Notification",
        )
        messages.success(self.request, f"Notifikasaun haruka ba uza-na'in {count}.")
        return super().form_valid(form)
