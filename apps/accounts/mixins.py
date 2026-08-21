from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .nav import visible_nav_items


class DashboardAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.can_access_dashboard()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        raise PermissionDenied


class PermissionOrSuperuserMixin(DashboardAccessMixin):
    """Require one of the listed permissions, or superuser."""

    required_permissions: tuple[str, ...] = ()

    def test_func(self):
        if not super().test_func():
            return False
        user = self.request.user
        if user.is_superuser:
            return True
        if not self.required_permissions:
            return True
        return any(user.has_perm(perm) for perm in self.required_permissions)


class DashboardBaseMixin(DashboardAccessMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_items"] = visible_nav_items(self.request.user)
        context["user_roles"] = self.request.user.role_names()
        return context
