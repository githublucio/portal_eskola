from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, UpdateView

from .audit import log_action
from .mixins import DashboardBaseMixin, PermissionOrSuperuserMixin
from .models import AuditLog


def user_has_perm(user, perm):
    if not user or not user.is_authenticated or not perm:
        return False
    return user.is_superuser or user.has_perm(perm)


class StaffSectionMixin(DashboardBaseMixin, PermissionOrSuperuserMixin):
    pass


class DashboardFormMixin(StaffSectionMixin):
    template_name = "dashboard/form.html"
    form_title = ""
    form_intro = ""
    submit_label = "Rai"
    cancel_url_name = ""
    success_message = "Rai ona."
    audit_message = ""
    author_field = ""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_cancel_url(self):
        return reverse(self.cancel_url_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = self.form_title
        context["form_intro"] = self.form_intro
        context["submit_label"] = self.submit_label
        context["cancel_url"] = self.get_cancel_url()
        context["detail_rows"] = self.get_detail_rows()
        return context

    def get_detail_rows(self):
        return []

    def form_valid(self, form):
        is_new = form.instance.pk is None
        if self.author_field and not getattr(form.instance, f"{self.author_field}_id", None):
            setattr(form.instance, self.author_field, self.request.user)
        response = super().form_valid(form)
        log_action(
            user=self.request.user,
            action=AuditLog.Action.CREATE if is_new else AuditLog.Action.UPDATE,
            obj=self.object,
            message=self.audit_message or self.success_message,
            request=self.request,
        )
        messages.success(self.request, self.success_message)
        return response


class DashboardCreateView(DashboardFormMixin, CreateView):
    pass


class DashboardUpdateView(DashboardFormMixin, UpdateView):
    pass


class DashboardStatusDeleteView(StaffSectionMixin, DeleteView):
    """Confirm via GET; POST archives (preferred) or hard-deletes drafts only."""

    template_name = "dashboard/confirm_delete.html"
    cancel_url_name = ""
    prefer_archive = True
    allow_hard_delete = True
    status_field = "status"
    archive_value = "archived"
    draft_value = "draft"
    change_permission = ""
    delete_permission = ""
    archive_message = "Arkivu ona."
    delete_message = "Hamoos ona."

    def get_cancel_url(self):
        return reverse(self.cancel_url_name)

    def _status(self, obj):
        return getattr(obj, self.status_field, None)

    def _can_hard_delete(self, user, obj):
        if not self.allow_hard_delete:
            return False
        if not user_has_perm(user, self.delete_permission):
            return False
        if self.prefer_archive:
            return self._status(obj) == self.draft_value
        return True

    def _can_archive(self, user, obj):
        if not self.prefer_archive:
            return False
        if self._status(obj) == self.archive_value:
            return False
        return user_has_perm(user, self.change_permission)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context["object"]
        hard = self._can_hard_delete(self.request.user, obj)
        context["cancel_url"] = self.get_cancel_url()
        if hard:
            context["confirm_title"] = "Konfirma hamoos"
            context["confirm_label"] = "Hamoos"
            context["confirm_message"] = (
                "Asaun ne'e sei hamoos permanente raskunhu ne'e. La bele fila fali."
            )
        else:
            context["confirm_title"] = "Konfirma arkivu"
            context["confirm_label"] = "Arkivu"
            context["confirm_message"] = (
                "Asaun ne'e sei arkiva item ne'e. Ita bele hadia fali iha futuru."
            )
        return context

    def _can_act(self, user, obj):
        return self._can_hard_delete(user, obj) or self._can_archive(user, obj)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self._can_act(request.user, self.object):
            messages.error(request, "La bele hamoos ka arkiva item ne'e.")
            return redirect(self.get_cancel_url())
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        obj = self.object
        user = self.request.user
        success_url = self.get_success_url()
        if self._can_hard_delete(user, obj):
            log_action(
                user=user,
                action=AuditLog.Action.DELETE,
                obj=obj,
                message=self.delete_message,
                request=self.request,
            )
            try:
                obj.delete()
            except ProtectedError:
                messages.error(
                    self.request,
                    "La bele hamoos: sei iha ligasaun ba rejistu seluk.",
                )
                return redirect(self.get_cancel_url())
            messages.success(self.request, self.delete_message)
            return redirect(success_url)

        setattr(obj, self.status_field, self.archive_value)
        obj.save()
        log_action(
            user=user,
            action=AuditLog.Action.UPDATE,
            obj=obj,
            message=self.archive_message,
            request=self.request,
        )
        messages.success(self.request, self.archive_message)
        return redirect(success_url)
